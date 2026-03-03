"""
Common English stop words filtered out of trend topic extraction.

Any topic token that appears in this set is excluded from trend results
to prevent generic words from dominating the trending topics list.
"""

STOP_WORDS = {
    "the", "a", "an", "is", "in", "it", "of", "to", "and", "for",
    "with", "that", "this", "was", "are", "on", "at", "by", "or",
    "be", "as", "its", "not", "but", "from", "have", "had", "has",
    "do", "did", "doing", "done", "get", "got", "getting", "just",
    "been", "my", "your", "their", "our", "we", "they", "i", "he",
    "she", "you", "me", "him", "her", "us", "them", "what", "how",
    "when", "where", "who", "which", "will", "would", "could", "should",
    "can", "may", "might", "also", "more", "so", "if", "then", "than",
    "no", "yes", "all", "any", "some", "up", "out", "about", "like",
    "faster", "better", "good", "great", "really", "very", "much",
    "still", "already", "other", "new", "old", "way", "use", "used",
    "using", "make", "made", "makes", "want", "wants", "wanted", "need",
    "needs", "needed", "see", "saw", "seen", "know", "knew", "known",
    "think", "thought", "go", "went", "gone", "come", "came", "look",
    "looking", "looked", "find", "found", "take", "took", "taken",
    "give", "gave", "given", "keep", "kept", "try", "tried", "trying",
    "work", "works", "worked", "working", "say", "said", "says", "time",
    "day", "year", "week", "month", "people", "thing", "things",
}
