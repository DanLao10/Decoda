"""Sample passages grouped by grade band for the Decoda reader."""
from __future__ import annotations

SAMPLES: dict[str, list[dict]] = {
    "K-2 (Ages 5-7)": [
        {
            "title": "The Lost Kitten",
            "text": (
                "Lily found a kitten in the yard.\n"
                "It was small and gray.\n"
                "The kitten was wet from the rain.\n\n"
                "Lily made a warm bed with an old towel.\n"
                "She gave the kitten some milk.\n"
                "Soon the kitten fell asleep.\n\n"
                "Lily smiled. She had a new friend."
            ),
        },
        {
            "title": "At the Park",
            "text": (
                "Sam went to the park with his dad.\n"
                "He ran to the swings first.\n"
                "Up and down. Up and down.\n\n"
                "Then Sam climbed the big slide.\n"
                "Whee! He slid down fast.\n\n"
                "At the end, Sam was tired.\n"
                "He held his dad's hand and went home."
            ),
        },
    ],
    "3-5 (Ages 8-10)": [
        {
            "title": "How Bees Help Us",
            "text": (
                "Bees are small, but they do a big job.\n"
                "They fly from flower to flower looking for nectar.\n"
                "While they drink, yellow dust called pollen sticks to their bodies.\n\n"
                "When a bee lands on the next flower, some pollen rubs off.\n"
                "This helps the flower make seeds and fruit.\n"
                "Without bees, we would have far less food to eat.\n\n"
                "That is why people plant gardens that bees love.\n"
                "Sunflowers, lavender, and clover all give bees what they need."
            ),
        },
        {
            "title": "The Coldest Place on Earth",
            "text": (
                "Antarctica is the coldest place on Earth.\n"
                "It is covered in thick ice all year long.\n"
                "Even in summer, the temperature stays below freezing.\n\n"
                "Only a few animals can live there.\n"
                "Penguins waddle on the ice and dive for fish.\n"
                "Seals rest on the snow and swim under the sea.\n\n"
                "No people live in Antarctica all the time.\n"
                "But scientists visit to study the ice and the weather."
            ),
        },
    ],
    "6-8 (Ages 11-13)": [
        {
            "title": "Why the Sky Is Blue",
            "text": (
                "Sunlight looks white, but it is actually a mix of every color.\n"
                "When light from the Sun reaches our atmosphere, it crashes into\n"
                "tiny molecules of air. These molecules scatter the light in every direction.\n\n"
                "Blue light scatters much more than red or yellow light because it travels\n"
                "in shorter waves. That scattered blue light reaches our eyes from every\n"
                "part of the sky, which is why the sky looks blue during the day.\n\n"
                "At sunset, the light has to travel through more air to get to us.\n"
                "Most of the blue is scattered away, leaving the warmer reds and oranges\n"
                "we see on the horizon."
            ),
        },
        {
            "title": "The First Olympic Games",
            "text": (
                "The first recorded Olympic Games were held in Greece in 776 BCE.\n"
                "They took place in a small town called Olympia, on a plain by a river.\n"
                "Only Greek men could compete, and the events lasted just one day.\n\n"
                "The original program was simple: a footrace of about 200 meters.\n"
                "Over the next few centuries, organizers added wrestling, boxing,\n"
                "chariot races, and a brutal mixed combat sport called pankration.\n\n"
                "Winners did not receive gold medals. Instead, they were crowned with\n"
                "a wreath of olive leaves and treated as heroes when they returned home."
            ),
        },
    ],
    "9-12 (Ages 14-18)": [
        {
            "title": "How Vaccines Work",
            "text": (
                "A vaccine is a careful introduction. It shows your immune system a\n"
                "harmless piece of a virus or bacterium — a fragment of its surface,\n"
                "or a weakened version that cannot make you sick.\n\n"
                "Your immune system reacts as if it were under attack. It builds\n"
                "specialized proteins called antibodies and trains memory cells that\n"
                "remember exactly what the threat looks like.\n\n"
                "If the real pathogen ever shows up, your body recognizes it almost\n"
                "immediately. The memory cells multiply, antibodies flood your bloodstream,\n"
                "and the infection is usually stopped before it can take hold.\n\n"
                "This is why vaccinated people can still encounter a virus and not get sick,\n"
                "or only experience a much milder version of the illness."
            ),
        },
        {
            "title": "The Idea of Supply and Demand",
            "text": (
                "Supply and demand is one of the oldest ideas in economics, and it explains\n"
                "why prices change. Supply is how much of something is available; demand is\n"
                "how much people want to buy.\n\n"
                "When demand grows faster than supply — think concert tickets for a popular\n"
                "artist — prices rise. Sellers know buyers are competing for a limited number\n"
                "of seats, so they can charge more.\n\n"
                "When supply outpaces demand — like winter coats in July — prices drop.\n"
                "Stores would rather sell at a discount than be stuck holding inventory.\n\n"
                "Most prices in a market settle near a point where supply and demand are\n"
                "roughly equal. Economists call this the equilibrium price."
            ),
        },
    ],
}


def grade_bands() -> list[str]:
    return list(SAMPLES.keys())


def titles_for(band: str) -> list[str]:
    return [s["title"] for s in SAMPLES.get(band, [])]


def get_sample(band: str, title: str) -> str:
    for s in SAMPLES.get(band, []):
        if s["title"] == title:
            return s["text"]
    return ""
