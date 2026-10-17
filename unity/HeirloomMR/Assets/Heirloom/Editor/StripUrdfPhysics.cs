using System.Linq;
using UnityEditor;
using UnityEngine;

namespace Heirloom.EditorTools
{
    /// <summary>
    /// Removes the URDF importer's physics (ArticulationBodies, colliders, importer scripts) from a robot,
    /// leaving a plain hierarchy of meshes the brain can pose directly. Undoable.
    /// </summary>
    public static class StripUrdfPhysics
    {
        [MenuItem("Heirloom/Strip URDF Physics From Selected")]
        static void Strip()
        {
            var root = Selection.activeGameObject;
            if (root == null)
            {
                Debug.LogWarning("[Heirloom] Select the robot's root object in the Hierarchy first.");
                return;
            }

            int removed = 0;

            // 1. Importer scripts first, since they depend on the ArticulationBodies.
            foreach (var mb in root.GetComponentsInChildren<MonoBehaviour>(true))
            {
                var ns = mb != null ? mb.GetType().Namespace : null;
                if (ns != null && ns.StartsWith("Unity.Robotics"))
                {
                    Undo.DestroyObjectImmediate(mb);
                    removed++;
                }
            }

            // 2. ArticulationBodies, deepest first.
            foreach (var ab in root.GetComponentsInChildren<ArticulationBody>(true).Reverse().ToArray())
            {
                Undo.DestroyObjectImmediate(ab);
                removed++;
            }

            // 3. Colliders.
            foreach (var c in root.GetComponentsInChildren<Collider>(true))
            {
                Undo.DestroyObjectImmediate(c);
                removed++;
            }

            Debug.Log($"[Heirloom] Removed {removed} physics components from '{root.name}'.");
        }
    }
}
