from __future__ import annotations

from time import sleep

from main import MotionMode, VibrationTable


TEST_ADDRESS = "192.168.3.7"
TEST_PORT = 8887
TEST_DURATION = 2.0


def connection_check() -> None:
    assert VibrationTable.can_connect(TEST_ADDRESS, TEST_PORT)


def light_control() -> None:
    table = VibrationTable(TEST_ADDRESS, TEST_PORT)
    table.light_on(800)
    sleep(TEST_DURATION)
    table.light_off()


def center_vibration() -> None:
    table = VibrationTable(TEST_ADDRESS, TEST_PORT)
    table.start_vibration(MotionMode.CenterHorizontal)
    sleep(TEST_DURATION)
    table.stop_vibration()


if __name__ == "__main__":
    connection_check()
    center_vibration()
    light_control()
    print("device tests passed")
