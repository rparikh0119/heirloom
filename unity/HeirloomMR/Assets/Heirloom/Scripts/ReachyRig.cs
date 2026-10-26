using UnityEngine;

namespace Heirloom
{
    /// <summary>
    /// Poses the imported Reachy Mini model from Heirloom channels.
    /// The head is posed directly (no linkage simulation). Reachy is a test body:
    /// the custom droid will get its own rig script that reads the same Channels.
    /// Run Heirloom > Strip URDF Physics From Selected on the robot first.
    /// </summary>
    public class ReachyRig : MonoBehaviour
    {
        [Header("Links (found by name if left empty)")]
        public Transform baseLink;      // body_down_3dprint (turns with base_yaw)
        public Transform head;          // xl_330
        public Transform antennaLeft;   // dc15_a01_horn_dummy_8
        public Transform antennaRight;  // dc15_a01_horn_dummy_7

        [Header("Directions (flip a sign if a channel moves the wrong way)")]
        public float pitchSign = -1f;
        public float yawSign = -1f;
        public float rollSign = 1f;
        public float baseYawSign = -1f;
        public float antennaSign = 1f;

        [Header("Axes, in the robot root's space (the way the robot faces)")]
        public Vector3 pitchAxis = Vector3.right;
        public Vector3 yawAxis = Vector3.up;
        public Vector3 rollAxis = Vector3.forward;
        [Tooltip("In each antenna's own local space")]
        public Vector3 antennaAxis = Vector3.up;

        [Tooltip("Let the brain roll the robot across the desk (drive_x / drive_z). The lab Reachy can't really roll, so this is MR only.")]
        public bool canRoll = true;

        [Tooltip("Hide the Stewart rods, since the head is posed directly and they won't follow it.")]
        public bool hideLinkage = true;

        [Header("Preview (Play mode): overrides the brain while ticked")]
        public bool preview;
        public Channels previewPose = new Channels();

        public Channels Current { get; private set; } = new Channels();

        /// <summary>Head position at rest, in world space. The brain measures the user from here.</summary>
        public Vector3 HeadRestWorld => transform.TransformPoint(_headRestInRoot);

        Vector3 _headRestInRoot;
        Vector3 _homePos;          // where it started on the desk. Rolling is measured from here
        Quaternion _homeRot;

        Quaternion _headRest, _baseRest, _antLRest, _antRRest;
        Vector3 _pitchB, _yawB, _rollB, _baseUpP;   // axes converted into the frames we rotate in
        bool _ready;

        void Awake()
        {
            if (!baseLink) baseLink = FindChild("body_down_3dprint");
            if (!head) head = FindChild("xl_330");
            if (!antennaLeft) antennaLeft = FindChild("dc15_a01_horn_dummy_8");
            if (!antennaRight) antennaRight = FindChild("dc15_a01_horn_dummy_7");

            if (!baseLink || !head)
            {
                Debug.LogError("[Heirloom] ReachyRig could not find body_down_3dprint or xl_330. Assign them in the Inspector.");
                return;
            }

            // Detach the head from the Stewart linkage so it can be posed directly.
            if (head.parent != baseLink) head.SetParent(baseLink, true);

            if (hideLinkage)
            {
                foreach (var t in baseLink.GetComponentsInChildren<Transform>(true))
                {
                    if (!t.name.StartsWith("dc15_a01_horn_dummy")) continue;
                    if (t == antennaLeft || t == antennaRight || t.IsChildOf(head)) continue;
                    foreach (var r in t.GetComponentsInChildren<Renderer>(true)) r.enabled = false;
                }
            }

            _homePos = transform.position;
            _homeRot = transform.rotation;
            _headRest = head.localRotation;
            _baseRest = baseLink.localRotation;
            _headRestInRoot = transform.InverseTransformPoint(head.position);

            // The URDF's internal link frames point in arbitrary directions, so express every axis
            // relative to the robot root (which faces the way you see it) and convert once at rest.
            var toBase = Quaternion.Inverse(baseLink.rotation) * transform.rotation;
            _pitchB = toBase * pitchAxis.normalized;
            _yawB = toBase * yawAxis.normalized;
            _rollB = toBase * rollAxis.normalized;
            var baseParent = baseLink.parent ? baseLink.parent.rotation : Quaternion.identity;
            _baseUpP = Quaternion.Inverse(baseParent) * transform.rotation * yawAxis.normalized;
            if (antennaLeft) _antLRest = antennaLeft.localRotation;
            if (antennaRight) _antRRest = antennaRight.localRotation;
            _ready = true;
        }

        void Update()
        {
            if (preview) Apply(previewPose, fromPreview: true);
        }

        /// <summary>Called by HeirloomLink for every pose frame from the brain.</summary>
        public void Apply(Channels c) => Apply(c, fromPreview: false);

        void Apply(Channels c, bool fromPreview)
        {
            if (!_ready || c == null) return;
            if (preview && !fromPreview) return;
            Current = c;

            if (canRoll)   // slides on the desk. Everything that follows the robot (overlays, beam, your distance) comes along
                transform.position = _homePos + _homeRot * new Vector3(c.drive_x, 0f, c.drive_z);

            baseLink.localRotation = Quaternion.AngleAxis(baseYawSign * c.base_yaw, _baseUpP) * _baseRest;

            head.localRotation =
                Quaternion.AngleAxis(yawSign * c.head_yaw, _yawB) *
                Quaternion.AngleAxis(pitchSign * c.head_pitch, _pitchB) *
                Quaternion.AngleAxis(rollSign * c.head_roll, _rollB) *
                _headRest;

            if (antennaLeft) antennaLeft.localRotation = _antLRest * Quaternion.AngleAxis(antennaSign * c.antenna_left, antennaAxis);
            if (antennaRight) antennaRight.localRotation = _antRRest * Quaternion.AngleAxis(antennaSign * c.antenna_right, antennaAxis);
        }

        Transform FindChild(string n)
        {
            foreach (var t in GetComponentsInChildren<Transform>(true))
                if (t.name == n) return t;
            return null;
        }
    }
}
