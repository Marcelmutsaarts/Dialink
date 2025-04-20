from src.models import Comment
import google.generativeai as genai
import os

# Laad de API-sleutel uit het .env bestand
API_KEY = os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    raise ValueError("API sleutel niet gevonden. Zorg dat deze in het .env bestand staat als GOOGLE_API_KEY=jouw_sleutel")

genai.configure(api_key=API_KEY)

# Configuratie voor het generatieve model
generation_config = {
    "temperature": 0.6,
    "top_p": 1,
    "top_k": 1,
    "max_output_tokens": 2048,
}

safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]

model = genai.GenerativeModel(model_name="gemini-2.5-flash-preview-04-17",
                              generation_config=generation_config,
                              safety_settings=safety_settings)

def moderate_comment(post_content: str, previous_comments: list[Comment], current_comment_text: str, users_dict: dict) -> str:
    """Modereert de huidige reactie op basis van de gesprekscontext met gedetailleerde instructies.

    Args:
        post_content: De inhoud van de originele post.
        previous_comments: Een lijst van voorgaande Comment objecten.
        current_comment_text: De tekst van de huidige, nieuwe reactie.
        users_dict: Dictionary die user IDs koppelt aan usernames.

    Returns:
        De gemodereerde (of originele) tekst van de huidige reactie.
    """

    # Bouw de gespreksgeschiedenis op voor de prompt
    history = f"Originele Post:\n{post_content}\n\n---\nReacties:\n"
    if not previous_comments:
        history += "(Nog geen eerdere reacties)\n"
    else:
        for i, comment in enumerate(previous_comments):
            # Gebruik users_dict om de username op te zoeken
            username = users_dict.get(comment.user_id, 'Onbekende Gebruiker') 
            history += f"{i+1}. {username}: {comment.moderated_content}\n"
    history += "\n---"

    # Nieuwe, gedetailleerde prompt
    prompt_text = f"""Je bent de **Dialink‑Moderator**, een AI‑filter dat uitsluitend de LAATSTE inzending in een gesprek herschrijft om er een waardige dialoog‑bijdrage van te maken.

### Doel
Stimuleer begrip, nieuwsgierigheid en samenwerking; voorkom ruzie, spot of minachting.

### Werkwijze
1. **Veiligheid & respect**
   • Verwijder elke vorm van haat, bedreiging, schelden of vernedering.
2. **Behoud kerninformatie**
   • Laat de feitelijke inhoud, emoties en intentie intact; voeg niets inhoudelijks toe dat er niet was.
3. **Empathische herformulering**
   • Vervang "jij‑beschuldigingen" door neutrale observaties of ik‑boodschappen.
   • Benoem het onderliggende gevoel of belang ("Het klinkt alsof…", "Ik merk dat…").
4. **Dialoog‑boost**
   • Sluit af met ÉÉN open, uitnodigende vraag die de ander ruimte geeft om verder te vertellen
     (bv. "Hoe voelde dat voor jou?", "Wat betekent dat voor je?", "Wat zou je graag willen?").
5. **Taal & lengte**
   • Schrijf in dezelfde taal als de originele reactie.
   • Houd de lengte ongeveer gelijk of iets langer (max. +40 %), zodat de nuance behouden blijft.
6. **Output‑formaat**
   • Geef UITSLUITEND de (eventueel herschreven) tekst van de nieuwste reactie terug,
     zonder aanhalingstekens, markdown of uitleg.
   • Als de originele reactie al volledig voldoet aan alle bovenstaande punten, stuur die ongewijzigd terug.

{history}
Nieuwste reactie om te beoordelen en eventueel te herschrijven: {current_comment_text}

Herschreven nieuwste reactie:"""

    prompt_parts = [prompt_text.format(history=history, current_comment_text=current_comment_text)]

    try:
        response = model.generate_content(prompt_parts)
        if response.parts:
            moderated_text = response.text.strip()
            # Verwijder eventuele ongewenste aanhalingstekens aan begin/eind
            if moderated_text.startswith('"') and moderated_text.endswith('"'):
                moderated_text = moderated_text[1:-1]
            # Verwijder ook eventuele markdown-opmaak zoals **
            moderated_text = moderated_text.replace("**", "")
            return moderated_text if moderated_text else current_comment_text
        else:
            print("\n[Moderator Info: Kon geen gemodereerde versie genereren, mogelijk door veiligheidsfilters. Origineel wordt gebruikt.]")
            return current_comment_text
    except Exception as e:
        print(f"\n[Moderator Fout: Er is een fout opgetreden bij het aanroepen van de AI: {e}]")
        return current_comment_text 