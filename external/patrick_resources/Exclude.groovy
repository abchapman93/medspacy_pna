import gov.va.vinci.leo.regex.types.RegularExpressionType

/* An arbitrary name for this annotator. Used in the pipeline for the name of this annotation. */
name = "Exclude Terms"

configuration {
    /* All configuration for this annotator. */
    defaults {
        /* Global for all configrations below if a property specified here is not overridden in a section below. */

        outputType = RegularExpressionType.class.canonicalName
        case_sensitive = false
        matchedPatternFeatureName = "pattern"
        concept_feature_name = "concept"
        groupFeatureName = "group"
    }

    "pneumonia_exclude"  {
        expressions = [
                //Common Templates and Titles
               'What can I do to keep from getting',
                'These medicines kill the germs that cause',
                'is\\s*this\\s*a\\s*pneumonia\\s*patient',
                'pneumonia\\s*suspected\\?\\s*no',
                'Is this Diagnosis Pneumonia or Rule Out Pneumonia',
                '\\(pneumonia & Septic patients only',
                'recent\\s*treatmemt\\s*for',
                'did\\s*not\\s*feel\\s*that\\s*this\\s*represented\\s*pneumonia',
                'Airspace disease; possibility of right lung base',
                //IRRELEVENT PNEUMONIA TERMS
                'vaccine',
                'asses\\s*for',
                'test\\s*for',
                'problem\\s*list\\s*is\\s*the\\s*source\\s*for\\s*the\\s*following\\s*:\\s*1\\.\\s*',
                'vaccination',
                //OTHER EXCLUSIONS
                'Pt concerned that he might have a',
                'recent\\s*treatment\\s*for',
                //possible, may set other value, exclude for now
                //'possible',
                'is\\s*a\\s*possibility',
                //Differential
                'DDX:?',
                'DDX\\s*includes',
                'ddx',
                'differential\\s*diagnosis',
                'didn\'?t\\s*show\\s*(any|signs\\s*of)',
                'didn\'?t\\s*show',
                'doesn\'?t\\s*show\\s*(any|signs\\s*of)',
                'doesn\'?t\\s*show',
                'does\\s*not\\s*show\\s*any',
                'might\\s*represent',
                'suspicion\\s*for\\s*underlying',
                'r/o',
                //Patient Assertion
                'i\\s*think\\s*I\\s*have',
                'pt\\s*states\\s*that\\s*s?he\\s*has',
                //PMH
                'was\\s*diagnosed\\s*with',
                'could\\s*be\\s*(septic\\s*)?from',
                'historical\\s*data',
                //Needs likely Pneumonia Pattern annotator
                'hc\\s*of',
                'no\\s*(abx|antibiotics)',
                'no\\s*(abx|antibiotics)\\s*for',
                'current\\s*pneumonia\\s*unknown',
                'hx\\s*of\\s*aspiration',
                'help\\s*pervent\\s*pneumonia',
                'low\\s*suspicion\\s*for',
                'low\\s*clinical\\s*suspicion\\s*for',
                'could\\s*be\\s*septic\\s*from',
                'this\\s*will\\s*help\\s*prevent',
                'not\\s*ruled\\s*out',
                'other\\s*meds:',
                'absc?ence\\s*of',
                //PMH headers as exclusions
                '(past )?medica\\s+(history|hx)',
                '\\bmhx?',
                'mh/pshx',
                '\\bmh:?',
                'pohx',
                'pmh:?',
                'pmh[sx]',
                'pmhx\\/pshx',
                'past\\s*history:',
                'history:',
                'p[hm]+:\\s*computerized\\s+problem\\s+list',
                'significant\\smedical\\shx:',
                'past\\smedical\\shistory\\s?\\/\\s?problem list',
                'pneumonia\\s*(abx|antibiotics)',
                'what\\s*are\\s*the\\s*symptoms\\s*of'

        ]
        concept_feature_value = "Exclude"
        outputType = "gov.va.vinci.types.Exclude"
    }

}







