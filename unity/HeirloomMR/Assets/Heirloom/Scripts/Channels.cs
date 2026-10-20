namespace Heirloom
{
    /// <summary>Heirloom body channels (see docs/architecture.md). Degrees for angles, 0..1 for iris and light.</summary>
    [System.Serializable]
    public class Channels
    {
        [UnityEngine.Range(-35, 35)] public float head_pitch;     // + looks up
        [UnityEngine.Range(-70, 70)] public float head_yaw;       // + looks left
        [UnityEngine.Range(-30, 30)] public float head_roll;      // + tilts left
        [UnityEngine.Range(-160, 160)] public float base_yaw;       // + turns left
        [UnityEngine.Range(-90, 90)] public float antenna_left;   // 0 upright
        [UnityEngine.Range(-90, 90)] public float antenna_right;  // 0 upright
        [UnityEngine.Range(0, 1)] public float iris = 0.6f;    // 0 closed .. 1 wide
        [UnityEngine.Range(0, 1)] public float light = 0.5f;   // 0 off .. 1 full
    }
}
