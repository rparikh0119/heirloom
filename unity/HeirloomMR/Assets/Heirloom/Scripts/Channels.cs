namespace Heirloom
{
    /// <summary>Heirloom body channels (see docs/architecture.md). Degrees for angles, 0..1 for iris and light.</summary>
    [System.Serializable]
    public class Channels
    {
        public float head_pitch;     // + looks up
        public float head_yaw;       // + looks left
        public float head_roll;      // + tilts left
        public float base_yaw;       // + turns left
        public float antenna_left;   // 0 upright
        public float antenna_right;  // 0 upright
        public float iris = 0.6f;    // 0 closed .. 1 wide
        public float light = 0.5f;   // 0 off .. 1 full
    }
}
