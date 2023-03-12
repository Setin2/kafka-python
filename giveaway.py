from instabot import Bot
import os
import random
from dotenv import load_dotenv
import argparse
import math

def get_followers(username, bot):
    followers = bot.get_user_followers(username)
    return [(None, username) for username in followers]

def get_followed_users(username, users, bot):
    followers = bot.get_user_followers(username)
    followed_users = [username for user_id, username in users if str(user_id) in followers]
    return followed_users

def get_random_user(users):
    random_number = random.randint(0, len(users)-1)
    return users[random_number][1]

def main():
    parser = argparse.ArgumentParser(description='This is a Instagram giveaway '\
                                                 'winner checker.')
    parser.add_argument('username', help="Instagram username")
    args = parser.parse_args()
    username = args.username

    """load_dotenv()
    INSTA_USERNAME = os.getenv('INSTA_USERNAME')
    INSTA_PASSWORD = os.getenv('INSTA_PASSWORD')
    bot = Bot()
    bot.login(username=INSTA_USERNAME, password=INSTA_PASSWORD)
    followers = get_followers(username, bot)"""
    if True:
        #winner = get_random_user(followers)
        winner = "wtungk"
        print()
        print('\033[1m' + '\033[4m' + "The winner is:\n" + '\033[0m')
        print('\033[93m' + "* " * (len(winner) + 6) + '\033[0m')
        print(" " * (len(winner) + 2) + '\033[96m' + winner + '\033[0m')
        print('\033[93m' + "* " * (len(winner) + 6) + '\033[0m')
    else:
        print('No followers found')


if __name__ == '__main__':
    main()