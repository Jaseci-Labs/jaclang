enum 'Emotions'
emotion {
    Happy,
    Sad,
    Calm,
    Angry
}

node 'personality'
personality{
    has niceness: 'how nice the user is' int,
        likes : 'what kind of things they like' list[str],
        currentMood: 'current mood of the user' emotion;
}

walker 'users personal journal '
journal {
    has count: 'Daily Entry Count' int;
}

can add -> 'number' int{}

can 'update user mood'
updateMood(mood: 'Mood' emotion, apple: 'Apple' str) -> 'mood selection' str{}