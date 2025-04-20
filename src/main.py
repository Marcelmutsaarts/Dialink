from src.models import Post, Comment
from src.moderation import moderate_comment
import time

def main():
    # Simuleer de eerste post
    poster = input("Naam van de poster: ")
    post_content = input("Inhoud van de post: ")
    main_post = Post(user=poster, content=post_content)
    print("\n------ Post Gemaakt ------")
    print(main_post)
    print("-------------------------\n")
    time.sleep(1)

    # Start de dialoog
    first_commentator = input("Naam van de eerste commentator: ")
    current_user = first_commentator # Start met de eerste commentator
    turn = 0

    while True:
        print(f"\n------ Beurt {turn + 1} ({current_user}) ------")
        try:
            comment_content = input(f"Reactie van {current_user} (typ 'stop' om te eindigen): ")
            if comment_content.lower() == 'stop':
                break

            print("\nOriginele reactie:", comment_content)
            print("Reactie wordt gemodereerd...")
            moderated_text = moderate_comment(comment_content)

            new_comment = Comment(user=current_user, content=moderated_text, original_content=comment_content)
            main_post.add_comment(new_comment)

            print("------ Reactie Toegevoegd ------")
            print(new_comment)
            print("-----------------------------")

            # Wissel van gebruiker voor de volgende beurt
            current_user = poster if current_user == first_commentator else first_commentator
            turn += 1
            time.sleep(0.5)

        except KeyboardInterrupt:
            print("\nDialoog gestopt.")
            break
        except Exception as e:
            print(f"\nEr is een onverwachte fout opgetreden: {e}")
            # Optioneel: probeer opnieuw of stop
            # break

    print("\n------ Volledige Gesprek ------")
    print(main_post)
    for comment in main_post.comments:
        print(comment)
    print("-----------------------------")

if __name__ == "__main__":
    main() 