TINYAYA_LANGUAGES_BY_REGION = {
    "South Asia": [
        "Telugu", "Marathi", "Bengali", "Tamil", "Hindi", 
        "Punjabi", "Gujarati", "Urdu", "Nepali"
    ],
    "Asia Pacific": [
        "Traditional Chinese", "Cantonese", "Vietnamese", "Tagalog", "Javanese", 
        "Khmer", "Thai", "Burmese", "Malay", "Korean", 
        "Lao", "Indonesian", "Simplified Chinese", "Japanese"
    ],
    "Europe": [
        "Catalan", "Galician", "Dutch", "Danish", "Finnish", 
        "Czech", "Portuguese", "French", "Lithuanian", "Slovak", 
        "Basque", "English", "Swedish", "Polish", "Spanish", 
        "Slovenian", "Ukrainian", "Greek", "Bokmål", "Romanian", 
        "Serbian", "German", "Italian", "Russian", "Irish", 
        "Hungarian", "Bulgarian", "Croatian", "Estonian", "Latvian", "Welsh"
    ],
    "Africa": [
        "Zulu", "Amharic", "Hausa", "Igbo", "Swahili", 
        "Xhosa", "Wolof", "Shona", "Yoruba", "Nigerian Pidgin", "Malagasy"
    ],
    "West Asia": [
        "Arabic", "Maltese", "Turkish", "Hebrew", "Persian"
    ]
}

TINYAYA_SUPPORTED_LANGUAGES = {
    lang for langs in TINYAYA_LANGUAGES_BY_REGION.values() for lang in langs
}

from transformers import AutoTokenizer, AutoModelForCausalLM
TINYAYA_GLOBAL_MODEL_ID = "CohereLabs/tiny-aya-global"
TINYAYA_GLOBAL_TOKENIZER = AutoTokenizer.from_pretrained(TINYAYA_GLOBAL_MODEL_ID)
TINYAYA_GLOBAL_MODEL = AutoModelForCausalLM.from_pretrained(
    TINYAYA_GLOBAL_MODEL_ID, device_map="auto"
)

from voxcpm import VoxCPM
VOXCPM2_MODEL = VoxCPM.from_pretrained("openbmb/VoxCPM2", load_denoiser=False)
TTS_SAMPLE_RATE = VOXCPM2_MODEL.tts_model.sample_rate

VOXCPM2_SUPPORTED_LANGUAGES = [
    "Arabic", "Burmese", "Simplified Chinese", "Traditional Chinese", "Danish", "Dutch", "English", "Finnish", "French", 
    "German", "Greek", "Hebrew", "Hindi", "Indonesian", "Italian", "Japanese", "Khmer", 
    "Korean", "Lao", "Malay", "Norwegian", "Polish", "Portuguese", "Russian", "Spanish", 
    "Swahili", "Swedish", "Tagalog", "Thai", "Turkish", "Vietnamese"
]
