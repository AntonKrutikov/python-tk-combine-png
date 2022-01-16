`traits.json`

Describe all Trait types with file paths and conditions. Also describe ordered/filtered collections.

```json
{
  // Type (group) of Trait. 
  // For example it can be "head", "body", "foot"
  // Contain 1 or more named traits inside
  "group": {
      // Name of Trait variant per group
      "trait" : {
          "weight": 1, //not used, always 1
          // File can be:
          // 1. String, contain single path
          // 2. [] of String, contain multiple paths
          // 3. Object with following attributes
          //    {
          //        "path": String or [] of String,
          //        "adapted-to": [] of String
          //    }
          // 4. [] of Objects from (3)
          "file" : "",
          // Exclude this Trait from result if other Trait names exists (match by "trait" in any group)
          "exclude" : ["",""]
      }
  }

}
```