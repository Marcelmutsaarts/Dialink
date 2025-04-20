# Dialink - Gespreksmoderator

Dit project is een eenvoudige simulatie van een sociaal netwerk waarbij reacties (comments) worden gemodereerd door een AI (Google Generative AI) om constructieve dialoog te bevorderen.

## Installatie

1.  **Clone of download dit project.**
2.  **Maak een virtuele omgeving (aanbevolen):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # Op Windows: venv\Scripts\activate
    ```
3.  **Installeer de benodigde pakketten:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Stel je Google API sleutel in:**
    *   Open het `.env` bestand.
    *   Vervang `YOUR_API_KEY_HERE` door je daadwerkelijke Google Generative Language API sleutel.
    *   Sla het bestand op.

## Gebruik

Voer het hoofdscript uit vanuit de hoofdmap van het project:

```bash
python -m src.main
```

Het script zal je vragen om:
1.  De naam van de gebruiker die de post plaatst.
2.  De inhoud van de post.
3.  De naam van de gebruiker die de eerste reactie plaatst.

Vervolgens start een interactieve loop:
*   De huidige gebruiker wordt gevraagd om een reactie te typen.
*   De reactie wordt naar de AI-moderator gestuurd.
*   De (mogelijk gemodereerde) reactie wordt getoond.
*   De beurt gaat naar de andere gebruiker (de oorspronkelijke poster of de commentator).
*   Typ 'stop' om de dialoog te beëindigen en het volledige gesprek te zien.

## Projectstructuur

*   `.env`: Bevat de Google API sleutel (niet meegeleverd in versiebeheer).
*   `requirements.txt`: Lijst van Python afhankelijkheden.
*   `README.md`: Dit bestand.
*   `src/`: Bevat de broncode.
    *   `__init__.py`: Maakt van `src` een Python package.
    *   `models.py`: Definieert de `Post` en `Comment` klassen.
    *   `moderation.py`: Bevat de logica voor de interactie met de Google Generative AI API voor moderatie.
    *   `main.py`: Het hoofdscript om de simulatie uit te voeren. 