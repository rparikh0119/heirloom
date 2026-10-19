using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.XR.Hands;

namespace Heirloom
{
    /// <summary>
    /// Streams your hand joints to the brain, which spots the gestures (brain/heirloom/perception/gestures.py).
    /// Unity only measures. All the gesture logic lives in the brain, so it carries over to the robot's
    /// own camera in winter. Reads hands through Unity's XR Hands package (OpenXR "Hand Tracking Subsystem").
    /// Put this on the BrainLink object.
    /// </summary>
    public class HandStream : MonoBehaviour
    {
        public HeirloomLink link;
        public ReachyRig rig;

        [Tooltip("The camera rig's TrackingSpace. Leave empty to use the main camera's parent.")]
        public Transform trackingSpace;
        public float sendRate = 30f;

        [Tooltip("Draw a small dot on every joint the brain receives. Handy for checking the data lines up with your real hands.")]
        public bool showJoints = true;

        const int JointCount = 26;

        [Serializable]
        class HandsMessage
        {
            public string type = "hands";
            public bool left_tracked;
            public float[] left = new float[JointCount * 3];
            public bool right_tracked;
            public float[] right = new float[JointCount * 3];
        }

        readonly HandsMessage _msg = new HandsMessage();
        readonly List<XRHandSubsystem> _found = new List<XRHandSubsystem>();
        XRHandSubsystem _hands;
        Transform[] _dots;
        float _nextSend, _nextWarn;

        void Update()
        {
            if (link == null || rig == null) return;
            if (_hands == null || !_hands.running)
            {
                _hands = FindHands();
                if (_hands == null) return;
            }
            if (trackingSpace == null && Camera.main != null) trackingSpace = Camera.main.transform.parent;

            _msg.left_tracked = Read(_hands.leftHand, _msg.left, 0);
            _msg.right_tracked = Read(_hands.rightHand, _msg.right, JointCount);

            if (Time.time >= _nextSend)
            {
                _nextSend = Time.time + 1f / Mathf.Max(1f, sendRate);
                link.Send(JsonUtility.ToJson(_msg));
            }
        }

        XRHandSubsystem FindHands()
        {
            SubsystemManager.GetSubsystems(_found);
            foreach (var s in _found)
                if (s.running) return s;
            if (Time.time >= _nextWarn)
            {
                _nextWarn = Time.time + 10f;
                Debug.LogWarning("[Heirloom] HandStream: no running XR Hands subsystem. Check Project Settings > XR Plug-in Management > OpenXR (Windows tab) > Hand Tracking Subsystem.");
            }
            return null;
        }

        /// <summary>Fills buf with the hand's 26 joints in robot space. Returns false when the hand isn't tracked.</summary>
        bool Read(XRHand hand, float[] buf, int dotOffset)
        {
            bool tracked = hand.isTracked;
            for (int i = 0; i < JointCount; i++)
            {
                var id = XRHandJointIDUtility.FromIndex(i);   // 0 wrist, 1 palm, 2-5 thumb, 6-10 index...
                Vector3 robot = new Vector3(float.NaN, float.NaN, float.NaN);
                Vector3 world = Vector3.zero;
                Pose pose = default;
                bool ok = tracked && hand.GetJoint(id).TryGetPose(out pose);
                if (ok)
                {
                    world = trackingSpace != null ? trackingSpace.TransformPoint(pose.position) : pose.position;
                    // Same space the head uses: from the robot's resting head, in the robot's own axes.
                    robot = Quaternion.Inverse(rig.transform.rotation) * (world - rig.HeadRestWorld);
                }
                buf[i * 3] = robot.x;
                buf[i * 3 + 1] = robot.y;
                buf[i * 3 + 2] = robot.z;
                if (showJoints) Dot(dotOffset + i, ok, world);
            }
            return tracked;
        }

        void Dot(int index, bool visible, Vector3 world)
        {
            if (_dots == null)
            {
                _dots = new Transform[JointCount * 2];
                for (int i = 0; i < _dots.Length; i++)
                {
                    var go = GameObject.CreatePrimitive(PrimitiveType.Sphere);
                    Destroy(go.GetComponent<Collider>());
                    go.name = $"HandJoint{i}";
                    go.transform.SetParent(transform, false);
                    go.transform.localScale = Vector3.one * 0.008f;
                    go.GetComponent<Renderer>().material.color = i < JointCount ? new Color(0.5f, 0.7f, 0.85f) : new Color(0.75f, 0.5f, 0.8f);
                    _dots[i] = go.transform;
                }
            }
            _dots[index].gameObject.SetActive(visible);
            if (visible) _dots[index].position = world;
        }
    }
}
