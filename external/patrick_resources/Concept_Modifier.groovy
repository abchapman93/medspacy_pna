import gov.va.vinci.leo.regex.types.RegularExpressionType

/* An arbitrary name for this annotator. Used in the pipeline for the name of this annotation. */
name = "Pneumonia Noun Phrase Modifiers"

configuration {
    /* All configuration for this annotator. */
    defaults {
        /* Global for all configrations below if a property specified here is not overridden in a section below. */
        /*concept dictionaries modified from MEDEX*/
        outputType = RegularExpressionType.class.canonicalName
        case_sensitive = false
        matchedPatternFeatureName = "pattern"
        concept_feature_name = "concept"
        groupFeatureName = "group"
    }

    "Pneumonia) Types" {
        expressions = [
                'aspiration',
                'compatible',
                'associated',
                'superimposed',
                'bilateral',
                'left',
                'left-?sided',
                'right-?sided',
                'right',
                'atypical',
                'uti',
                'bacterial',
                'viral',
                'healthcare\\s*associated',
                'community(\\s*|-)acquired',
                'hap',
                'multilobar',
                'lower\\s*lobe',
                'blossoming',
                'underlying'
        ]
        concept_feature_value = "Modifer"
        outputType = "gov.va.vinci.types.ConceptModifier"
    }
}





