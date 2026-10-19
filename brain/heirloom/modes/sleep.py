from .base import Mode

SLEEP_POSE = {"head_pitch": -22, "head_yaw": 0, "head_roll": 4, "base_yaw": 0,
              "antenna_left": -40, "antenna_right": -40, "iris": 0.03, "light": 0.08}


class Sleep(Mode):
    """Head down, iris nearly closed. Ignores everything until woken."""
    name = "sleep"
    blocks_by_default = True
    attentive = False
    ease_in, ease_out = 0.6, 1.5    # falls asleep slowly, wakes quickly

    def apply(self, ch, blend):
        for k, v in SLEEP_POSE.items():
            if k in ch:
                ch[k] += (v - ch[k]) * blend
