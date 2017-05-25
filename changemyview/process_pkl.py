"""
File that processes the raw pickle files from the SRCC
"""

import re
import pandas as pd
import feather
from nltk.sentiment.vader import SentimentIntensityAnalyzer

SID = SentimentIntensityAnalyzer()
LINK_RE = re.compile(r"http\S*")


MOD_MES_RE = re.compile("\n_____\n\n.*")
re.sub(exp, '', top_submission.selftext)

def main():
    """
    Does transformations on cmv_auth_subs.pkl and cmv_subs.pkl
    """
    cmv_subs = pd.read_pickle("cmv_subs.pkl")
    cmv_auth_subs = pd.read_pickle("cmv_auth_subs.pkl")

    cmv_auth_subs = cmv_auth_subs[["sub_id", "title", "author", "created_utc", "content",
                                   "score", "subreddit"]]
    cmv_auth_subs["content"] = cmv_auth_subs.content.apply(
            lambda text: re.sub(MOD_MES_RE, "", text))
    cmv_auth_subs["deleted"] = cmv_auth_subs.content.str.contains(r"^\[deleted\]$")
    cmv_auth_subs["removed"] = cmv_auth_subs.content.str.contains(r"^\[removed\]$")
    cmv_auth_subs["empty"] = cmv_auth_subs.content.str.contains("^$")
    cmv_auth_subs["sentiment"] = cmv_auth_subs.content.apply(lambda text:
                                                             SID.polarity_scores(text)["compound"])
    cmv_auth_subs["url_link"] = cmv_auth_subs.content.apply(lambda text:
                                                            len(re.findall(LINK_RE, text)))
    cmv_auth_subs["cmv_sub"] = cmv_auth_subs.subreddit.apply(
        lambda subred: True if subred == "r/changemyview" else False)

    cmv_subs = cmv_subs.apply(pd.to_numeric, errors="ignore")
    cmv_auth_subs = cmv_auth_subs.apply(pd.to_numeric, errors="ignore")
    cmv_subs = cmv_subs[cmv_subs.title.str.contains("\[Podcast\]") == False]
    cmv_subs["content"] = cmv_subs.content.apply(
            lambda text: re.sub(MOD_MES_RE, "", text))
    cmv_subs["sentiment"] = cmv_subs.content.apply(lambda text:
                                                   SID.polarity_scores(text)["compound"])

    feather.write_dataframe(cmv_subs, "cmv_subs.feather")
    feather.write_dataframe(cmv_auth_subs, "cmv_auth_subs.feather")
    print("Feather files written")


if __name__ == "__main__":
    main()
