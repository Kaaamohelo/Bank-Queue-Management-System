import json
import subprocess
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

import queue_core


class QueueCoreTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.database_path = Path(self.temp_dir.name) / "queue_state.sqlite3"
        self.legacy_state_path = Path(self.temp_dir.name) / "queue_state.json"
        self.paths_patch = patch.multiple(
            queue_core,
            STATE_DB_PATH=self.database_path,
            LEGACY_STATE_PATH=self.legacy_state_path,
        )
        self.paths_patch.start()
        self.addCleanup(self.paths_patch.stop)
        self.write_legacy_state()
        queue_core.load_state()

    def write_legacy_state(
        self,
        waiting_queue=None,
        consultants=None,
        recent_calls=None,
        activity_log=None,
    ):
        state = {
            "waiting_queue": waiting_queue or [],
            "consultants": consultants or queue_core.default_consultants(),
            "recent_calls": recent_calls or [],
            "activity_log": activity_log or [],
        }
        self.legacy_state_path.write_text(json.dumps(state), encoding="utf-8")

    def test_new_ticket_with_idle_consultants_has_zero_wait(self):
        ticket, wait = queue_core.add_ticket("Open an account")

        self.assertEqual(wait, 0)
        self.assertEqual(ticket["ticket_number"], 1)

    def test_estimate_schedules_waiting_work_across_available_consultants(self):
        consultants = queue_core.default_consultants()
        consultants[0]["busy_for"] = 2
        consultants[1]["busy_for"] = 5
        for consultant in consultants[2:]:
            consultant["busy_for"] = 100
        waiting_queue = [
            {"ticket_number": 1, "service": "Credit enquiry"},
            {"ticket_number": 2, "service": "General enquiries"},
        ]
        self.database_path.unlink()
        self.write_legacy_state(waiting_queue=waiting_queue, consultants=consultants)
        queue_core.load_state()

        self.assertEqual(queue_core.estimate_wait_for_new_client(), 13)

    def test_serving_records_call_and_advancing_time_frees_consultant(self):
        ticket, _ = queue_core.add_ticket("Credit enquiry")

        served_ticket, consultant = queue_core.serve_next_client()
        self.assertEqual(served_ticket["ticket_number"], ticket["ticket_number"])
        self.assertEqual(served_ticket["status"], "Called")
        self.assertEqual(consultant["id"], 1)
        self.assertEqual(queue_core.recent_calls[0]["ticket_number"], 1)

        queue_core.advance_time(15)
        self.assertEqual(queue_core.consultants[0]["busy_for"], 0)
        self.assertIsNone(queue_core.consultants[0]["ticket"])
        self.assertEqual(queue_core.recent_calls[0]["status"], "Completed")

    def test_monitor_snapshot_includes_staff_queue_and_call_data(self):
        ticket, _ = queue_core.add_ticket("Credit enquiry")
        queue_core.serve_next_client()

        snapshot = queue_core.read_monitor_state()

        self.assertEqual(snapshot["waiting_queue"], [])
        self.assertEqual(
            snapshot["consultants"][0]["ticket"]["ticket_number"],
            ticket["ticket_number"],
        )
        self.assertEqual(snapshot["consultants"][0]["ticket"]["status"], "Called")
        self.assertEqual(snapshot["recent_calls"][0]["ticket_number"], 1)

    def test_cancel_removes_only_the_matching_waiting_ticket(self):
        first, _ = queue_core.add_ticket("Open an account")
        second, _ = queue_core.add_ticket("Credit enquiry")

        self.assertTrue(queue_core.cancel_ticket(first["ticket_number"]))
        self.assertFalse(queue_core.cancel_ticket(first["ticket_number"]))
        self.assertEqual(queue_core.waiting_queue, [second])

    def test_staff_activity_records_generic_actor_and_consultant_impact(self):
        active_ticket, _ = queue_core.add_ticket("Credit enquiry")
        queue_core.serve_next_client()
        waiting_ticket, _ = queue_core.add_ticket("General enquiries")

        queue_core.advance_time(3)
        queue_core.cancel_ticket(waiting_ticket["ticket_number"])
        queue_core.record_staff_action("Viewed waiting queue")

        activity_log = queue_core.read_monitor_state()["activity_log"]
        time_event = next(event for event in activity_log if event["action"] == "Advance time")
        cancel_event = next(event for event in activity_log if event["action"] == "Cancel ticket")
        call_event = next(event for event in activity_log if event["action"] == "Call next client")
        view_event = next(event for event in activity_log if event["action"] == "Viewed waiting queue")

        self.assertEqual(time_event["actor_label"], "Local staff")
        self.assertEqual(time_event["consultant_ids"], [1])
        self.assertEqual(time_event["ticket_numbers"], [active_ticket["ticket_number"]])
        self.assertEqual(cancel_event["actor_label"], "Local staff")
        self.assertEqual(cancel_event["consultant_ids"], [])
        self.assertEqual(cancel_event["ticket_number"], waiting_ticket["ticket_number"])
        self.assertEqual(
            cancel_event["details"],
            "No consultant assigned; waiting ticket removed",
        )
        self.assertEqual(call_event["actor_label"], "Local staff")
        self.assertEqual(view_event["actor_label"], "Local staff")

    def test_call_next_automatically_uses_each_next_free_consultant(self):
        first_ticket, _ = queue_core.add_ticket("Open an account")
        second_ticket, _ = queue_core.add_ticket("Credit enquiry")

        first_served, first_consultant = queue_core.serve_next_client()
        second_served, second_consultant = queue_core.serve_next_client()

        self.assertEqual(first_served["ticket_number"], first_ticket["ticket_number"])
        self.assertEqual(first_consultant["id"], 1)
        self.assertEqual(second_served["ticket_number"], second_ticket["ticket_number"])
        self.assertEqual(second_consultant["id"], 2)

    def test_ticket_issued_in_prototype_mode_is_attributed_to_local_staff(self):
        ticket, _ = queue_core.add_ticket("Open an account")

        event = queue_core.read_monitor_state()["activity_log"][0]
        self.assertEqual(event["action"], "Add ticket")
        self.assertEqual(event["ticket_number"], ticket["ticket_number"])
        self.assertEqual(event["actor_label"], "Local staff")

    def test_concurrent_ticket_creation_keeps_ticket_numbers_unique(self):
        with ThreadPoolExecutor(max_workers=8) as executor:
            tickets = list(executor.map(
                lambda task_index: queue_core.add_ticket("General enquiries")[0],
                range(32),
            ))

        ticket_numbers = sorted(ticket["ticket_number"] for ticket in tickets)
        self.assertEqual(ticket_numbers, list(range(1, 33)))

    def test_separate_processes_create_unique_tickets_in_shared_database(self):
        worker_code = "\n".join((
            "import sys",
            "from pathlib import Path",
            "import queue_core",
            "queue_core.STATE_DB_PATH = Path(sys.argv[1])",
            "queue_core.LEGACY_STATE_PATH = Path(sys.argv[2])",
            "ticket, estimated_wait = queue_core.add_ticket('General enquiries')",
            "print(ticket['ticket_number'])",
        ))
        processes = [
            subprocess.Popen(
                [
                    sys.executable,
                    "-c",
                    worker_code,
                    str(self.database_path),
                    str(self.legacy_state_path),
                ],
                cwd=Path(__file__).parent,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            for process_index in range(8)
        ]

        ticket_numbers = []
        for process in processes:
            stdout, stderr = process.communicate(timeout=30)
            self.assertEqual(process.returncode, 0, stderr)
            ticket_numbers.append(int(stdout.strip()))

        self.assertEqual(sorted(ticket_numbers), list(range(1, 9)))

    def test_public_calls_are_serialized_and_no_show_frees_consultant(self):
        first_ticket, _ = queue_core.add_ticket("Open an account")
        queue_core.serve_next_client()
        second_ticket, _ = queue_core.add_ticket("Credit enquiry")
        queue_core.serve_next_client()

        first_call = queue_core.get_next_public_call(now=100)
        self.assertEqual(first_call["ticket_number"], first_ticket["ticket_number"])
        self.assertEqual(first_call["attempt"], 1)
        self.assertEqual(queue_core.get_next_public_call(now=104), first_call)

        second_attempt = queue_core.get_next_public_call(now=105)
        self.assertEqual(second_attempt["attempt"], 2)
        third_attempt = queue_core.get_next_public_call(now=110)
        self.assertEqual(third_attempt["attempt"], 3)
        self.assertEqual(queue_core.get_next_public_call(now=119), third_attempt)

        next_call = queue_core.get_next_public_call(now=120)
        self.assertEqual(next_call["ticket_number"], second_ticket["ticket_number"])
        self.assertEqual(next_call["attempt"], 1)

        snapshot = queue_core.read_monitor_state()
        self.assertIsNone(snapshot["consultants"][0]["ticket"])
        self.assertEqual(snapshot["consultants"][0]["busy_for"], 0)
        missed_call = next(
            call for call in snapshot["recent_calls"]
            if call["ticket_number"] == first_ticket["ticket_number"]
        )
        self.assertEqual(missed_call["status"], "No-show")
        no_show_event = next(
            event for event in snapshot["activity_log"]
            if event["action"] == "No-show"
        )
        self.assertEqual(no_show_event["actor_label"], "Call timer")
        self.assertEqual(no_show_event["consultant_ids"], [1])

    def test_arrived_confirmation_stops_calls_and_advances_to_next_ticket(self):
        first_ticket, _ = queue_core.add_ticket("Open an account")
        queue_core.serve_next_client(consultant_id=3)
        second_ticket, _ = queue_core.add_ticket("Credit enquiry")
        queue_core.serve_next_client(consultant_id=4)
        queue_core.get_next_public_call(now=100)

        self.assertFalse(queue_core.mark_client_arrived(
            first_ticket["ticket_number"],
            consultant_id=4,
        ))
        self.assertTrue(queue_core.mark_client_arrived(
            first_ticket["ticket_number"],
            consultant_id=3,
        ))
        self.assertFalse(queue_core.mark_client_arrived(first_ticket["ticket_number"]))

        snapshot = queue_core.read_monitor_state()
        first_consultant_ticket = snapshot["consultants"][2]["ticket"]
        self.assertEqual(first_consultant_ticket["status"], "In service")
        first_call = next(
            call for call in snapshot["recent_calls"]
            if call["ticket_number"] == first_ticket["ticket_number"]
        )
        self.assertEqual(first_call["status"], "In service")

        next_call = queue_core.get_next_public_call(now=101)
        self.assertEqual(next_call["ticket_number"], second_ticket["ticket_number"])
        self.assertEqual(next_call["consultant_id"], 4)
        self.assertEqual(next_call["attempt"], 1)

    def test_legacy_json_import_preserves_source_and_ticket_sequence(self):
        self.database_path.unlink()
        legacy_queue = [{"ticket_number": 9, "service": "Credit enquiry"}]
        self.write_legacy_state(waiting_queue=legacy_queue)
        original_contents = self.legacy_state_path.read_bytes()

        queue_core.load_state()
        ticket, _ = queue_core.add_ticket("Open an account")

        self.assertEqual(ticket["ticket_number"], 10)
        self.assertEqual(self.legacy_state_path.read_bytes(), original_contents)

    def test_legacy_active_ticket_is_not_reannounced_as_a_new_call(self):
        consultants = queue_core.default_consultants()
        consultants[0]["busy_for"] = 8
        consultants[0]["ticket"] = {
            "ticket_number": 7,
            "service": "Credit enquiry",
        }
        self.database_path.unlink()
        self.write_legacy_state(consultants=consultants)
        queue_core.load_state()

        self.assertEqual(queue_core.consultants[0]["ticket"]["status"], "In service")
        self.assertIsNone(queue_core.get_next_public_call(now=100))

    def test_legacy_employee_audit_is_anonymized_for_prototype_mode(self):
        self.database_path.unlink()
        self.write_legacy_state(activity_log=[{
            "action": "Call next client",
            "actor_employee_number": "EMP-004721",
        }])
        queue_core.load_state()

        event = queue_core.read_monitor_state()["activity_log"][0]
        self.assertEqual(event["actor_label"], "Local staff")
        self.assertNotIn("actor_employee_number", event)


if __name__ == "__main__":
    unittest.main()