using UnityEngine;
using UnityEngine.Rendering;

namespace Heirloom
{
    /// <summary>
    /// The droid's projector in MR. When the brain shows a journal photo, a soft cone of light comes
    /// from the head and the photo lands flat on the real desk in front of the droid, warm and
    /// soft-edged like a real pico projector. A real image on a real surface, never a floating hologram.
    /// Put this on the robot (the object with ReachyRig) and assign its link.
    /// </summary>
    public class ProjectorBeam : MonoBehaviour
    {
        public HeirloomLink link;
        public ReachyRig rig;

        [Header("Where the photo lands (metres, relative to the robot's base)")]
        [Tooltip("How far in front of the robot, toward you")]
        public float distance = 0.28f;
        [Tooltip("Photo width on the desk")]
        public float width = 0.24f;
        [Tooltip("Lift above the desk so it doesn't flicker into it")]
        public float lift = 0.003f;

        [Header("Look")]
        [Tooltip("Projector lamp colour, multiplied into the photo")]
        public Color lamp = new Color(1f, 0.94f, 0.82f);
        [Range(0f, 1f)] public float beamStrength = 0.35f;
        [Tooltip("Where the light comes from, relative to the head at rest: right, up, forward")]
        public Vector3 lensOffset = new Vector3(0.025f, -0.02f, 0.05f);
        public float fadeSeconds = 0.6f;

        GameObject _photo, _beam;
        Material _photoMat, _beamMat;
        Mesh _beamMesh;
        Vector3 _lensInHead;
        float _shown, _target, _warmup;
        Texture2D _current;

        void Start()
        {
            if (rig == null) rig = GetComponent<ReachyRig>();
            if (link != null) link.Projected += OnProjected;

            _photoMat = MakeMaterial(additive: false);
            _beamMat = MakeMaterial(additive: true);
            _beamMat.SetTexture("_BaseMap", BeamGradient());

            _photo = new GameObject("Projected Photo");
            _photo.AddComponent<MeshFilter>().sharedMesh = PhotoQuad();
            _photo.AddComponent<MeshRenderer>().sharedMaterial = _photoMat;

            _beam = new GameObject("Projector Beam");
            _beamMesh = new Mesh { name = "beam" };
            _beam.AddComponent<MeshFilter>().sharedMesh = _beamMesh;
            _beam.AddComponent<MeshRenderer>().sharedMaterial = _beamMat;

            if (rig != null && rig.head != null)
                _lensInHead = rig.head.InverseTransformPoint(rig.HeadRestWorld + rig.transform.TransformVector(lensOffset));
            SetVisible(0f);
        }

        void OnDestroy()
        {
            if (link != null) link.Projected -= OnProjected;
        }

        void OnProjected(string photoName, Texture2D tex)
        {
            if (tex == null) { _target = 0f; return; }
            if (_current != null && _current != tex) Destroy(_current);
            _current = Soften(tex);
            if (tex != _current) Destroy(tex);
            _photoMat.SetTexture("_BaseMap", _current);
            _target = 1f;
            _warmup = 0.35f;     // a short lamp flicker as it switches on
        }

        void LateUpdate()
        {
            if (rig == null) return;
            _shown = Mathf.MoveTowards(_shown, _target, Time.deltaTime / Mathf.Max(0.05f, fadeSeconds));
            float flicker = 1f;
            if (_warmup > 0f) { _warmup -= Time.deltaTime; flicker = 0.55f + 0.45f * Mathf.PerlinNoise(Time.time * 40f, 0f); }
            SetVisible(_shown * flicker);
            if (_shown <= 0f) return;

            // The photo lies flat on the desk in front of the robot, readable from where you stand.
            var flatForward = Vector3.ProjectOnPlane(rig.transform.forward, Vector3.up).normalized;
            var rot = Quaternion.LookRotation(flatForward, Vector3.up);
            float aspect = _current != null ? (float)_current.height / _current.width : 0.75f;
            var center = rig.transform.position + flatForward * distance + Vector3.up * lift;
            _photo.transform.SetPositionAndRotation(center, rot);
            _photo.transform.localScale = new Vector3(width, 1f, width * aspect);

            // The cone: from the lens on the head to the photo's four corners.
            var lens = rig.head != null ? rig.head.TransformPoint(_lensInHead) : rig.HeadRestWorld;
            UpdateBeam(lens, center, rot, width, width * aspect);
        }

        void SetVisible(float a)
        {
            if (_photo == null) return;
            _photo.SetActive(a > 0.001f);
            _beam.SetActive(a > 0.001f);
            _photoMat.SetColor("_BaseColor", new Color(lamp.r, lamp.g, lamp.b, a));
            _beamMat.SetColor("_BaseColor", new Color(lamp.r, lamp.g, lamp.b, 1f) * (beamStrength * a));
        }

        // ---------- meshes ----------

        /// <summary>A 1x1 quad on the XZ plane. Its top edge (v = 1) faces the robot, so you read it the right way up.</summary>
        static Mesh PhotoQuad()
        {
            var m = new Mesh { name = "photo" };
            m.vertices = new[] { new Vector3(0.5f, 0, -0.5f), new Vector3(-0.5f, 0, -0.5f), new Vector3(-0.5f, 0, 0.5f), new Vector3(0.5f, 0, 0.5f) };
            // Seen from in front of the robot (you look toward -z), your right is the robot's left (-x).
            m.uv = new[] { new Vector2(0, 1), new Vector2(1, 1), new Vector2(1, 0), new Vector2(0, 0) };
            m.triangles = new[] { 0, 2, 1, 0, 3, 2 };
            m.RecalculateNormals();
            m.RecalculateBounds();
            return m;
        }

        void UpdateBeam(Vector3 lens, Vector3 center, Quaternion rot, float w, float h)
        {
            var c = new Vector3[4];
            c[0] = center + rot * new Vector3(w / 2, 0, -h / 2);
            c[1] = center + rot * new Vector3(-w / 2, 0, -h / 2);
            c[2] = center + rot * new Vector3(-w / 2, 0, h / 2);
            c[3] = center + rot * new Vector3(w / 2, 0, h / 2);
            // Four triangles, apex at the lens. UV v: 0 at the lens (bright) to 1 at the desk (faint).
            var verts = new Vector3[12];
            var uvs = new Vector2[12];
            var tris = new int[12];
            for (int i = 0; i < 4; i++)
            {
                verts[i * 3] = lens; verts[i * 3 + 1] = c[i]; verts[i * 3 + 2] = c[(i + 1) % 4];
                uvs[i * 3] = new Vector2(0.5f, 0f); uvs[i * 3 + 1] = new Vector2(0f, 1f); uvs[i * 3 + 2] = new Vector2(1f, 1f);
                tris[i * 3] = i * 3; tris[i * 3 + 1] = i * 3 + 1; tris[i * 3 + 2] = i * 3 + 2;
            }
            _beamMesh.Clear();
            _beamMesh.vertices = verts;
            _beamMesh.uv = uvs;
            _beamMesh.triangles = tris;
            _beamMesh.RecalculateBounds();
        }

        // ---------- textures and materials ----------

        /// <summary>Bakes a soft vignette into the photo, so its edges fade like a real projection.</summary>
        static Texture2D Soften(Texture2D src)
        {
            int w = src.width, h = src.height;
            var px = src.GetPixels32();
            var outTex = new Texture2D(w, h, TextureFormat.RGBA32, false) { wrapMode = TextureWrapMode.Clamp, name = src.name };
            for (int y = 0; y < h; y++)
            {
                float vy = Mathf.Min(y, h - 1 - y) / (h * 0.08f);
                for (int x = 0; x < w; x++)
                {
                    float vx = Mathf.Min(x, w - 1 - x) / (w * 0.08f);
                    float edge = Mathf.Clamp01(Mathf.Min(vx, vy));
                    var p = px[y * w + x];
                    p.a = (byte)(edge * edge * (3 - 2 * edge) * 235);      // smooth edge, a touch translucent
                    px[y * w + x] = p;
                }
            }
            outTex.SetPixels32(px);
            outTex.Apply();
            return outTex;
        }

        /// <summary>Alpha from bright at the lens to faint at the desk, for the beam.</summary>
        static Texture2D BeamGradient()
        {
            var t = new Texture2D(4, 64, TextureFormat.RGBA32, false) { wrapMode = TextureWrapMode.Clamp };
            for (int y = 0; y < 64; y++)
            {
                float v = y / 63f;
                float a = Mathf.Lerp(1f, 0.15f, Mathf.Sqrt(v));
                for (int x = 0; x < 4; x++) t.SetPixel(x, y, new Color(a, a, a, a));
            }
            t.Apply();
            return t;
        }

        /// <summary>URP Unlit, made transparent at runtime. Additive for light, alpha blended for the photo.</summary>
        static Material MakeMaterial(bool additive)
        {
            var shader = Shader.Find("Universal Render Pipeline/Unlit");
            var m = new Material(shader);
            m.SetFloat("_Surface", 1f);
            m.SetFloat("_Blend", additive ? 2f : 0f);
            m.SetFloat("_SrcBlend", (float)(additive ? BlendMode.One : BlendMode.SrcAlpha));
            m.SetFloat("_DstBlend", (float)(additive ? BlendMode.One : BlendMode.OneMinusSrcAlpha));
            m.SetFloat("_SrcBlendAlpha", (float)BlendMode.One);
            m.SetFloat("_DstBlendAlpha", (float)(additive ? BlendMode.One : BlendMode.OneMinusSrcAlpha));
            m.SetFloat("_ZWrite", 0f);
            m.SetFloat("_Cull", (float)CullMode.Off);
            m.EnableKeyword("_SURFACE_TYPE_TRANSPARENT");
            m.SetOverrideTag("RenderType", "Transparent");
            m.renderQueue = (int)RenderQueue.Transparent;
            return m;
        }
    }
}
