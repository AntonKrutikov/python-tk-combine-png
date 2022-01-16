`traits.json`

Describe all Trait types with file paths and conditions. Also describe ordered/filtered collections.

```jsonc
{
    // Describe ordered collections based on default collection, which contain all groups from this file.
    // Default collection will have index = 0 after parsing
    "_collections" : [
        {
            // Order of attributes in resulting NFT json file
            "_json_order": [],
            // If true - exclude not existed attribute in _json_order from resulting NFT json file. Note: this not affect image generation.
            "_json_order_exclusion": true,
            // Order of images (layers) for merge or displaying in gui
            "_image_order": [],
            // If true - exclude groups that not exists in _image_order from merge and gui
            "_image_order_exclusion": true
        }
        // ... more collections
    ],
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
        // ... more traits
    }
    // ... more groups
}
```