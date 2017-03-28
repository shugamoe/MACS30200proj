# Scraper for /r/changemyview data

import praw
from praw.models import Redditor
import os
import pandas as pd
import re
import numpy as numpy
import time


END_2016 = 1483228799
START_2013 = 1356998400

START_BDAY_2016 = 1461110400
END_BDAY_2016 = 1461196799


class CmvScraperModder:
    '''
    Class to scrape /r/changemyview for MACS 302 and possibly thesis.
    '''
    def __init__(self):
        '''
        Initializes the class with an instance of the praw.Reddit class.
        '''
        # PRAW objects
        self.praw_agent = praw.Reddit('cmv_scrape', # Site ID
            user_agent = '/u/shugamoe /r/changemyview scraper')
        self.subreddit = self.praw_agent.subreddit('changemyview')

        self.praw_agent.read_only = True # We're just here to look

        # Example instances to to tinker with
        self.eg_submission = self.praw_agent.submission('5kgxsz')
        self.eg_comment = self.praw_agent.comment('61saed')
        self.eg_user = self.praw_agent.redditor('shugamoe')

        # Dataframes
        self.cmv_subs = None
        self.cmv_author_coms = None
        self.cmv_author_subs = None

    def get_submissions(self, start, end):
        '''
        This function gathers the submission IDs for submissions in 
        /r/changemyview
        '''
        init_col_names = ['id', 'author', 'praw_inst']
        sub_df_dict = {col_name: [] for col_name in init_col_names}

        subs_gathered = 0
        for sub in self.subreddit.submissions(start, end):
            subs_gathered += 1
            sub_df_dict['author'].append(str(sub.author))
            sub_df_dict['id'].append(str(sub.id))
            sub_df_dict['praw_inst'].append(sub)

        print('{} submissions gathered'.format(subs_gathered))
        df = pd.DataFrame(sub_df_dict)
        self.cmv_subs = df.set_index('id', drop = False)

    def update_subs_df(self, start, end):
        '''
        This function retrieves following information about submissions:
            - Whether the OP awarded a delta
            - How many deltas the OP awarded
            - Number of top level replies
        '''
        if hasattr(self, 'subs_df'):
            pass
        else:
            self.get_submissions(start, end)

        all_subs = self.cmv_subs
        valid_subs = all_subs[all_subs['author'] != '[deleted]'][['praw_inst']]

        lambda_sub_info = lambda sub_inst: self.get_sub_info(sub_inst)
        valid_subs[list(CmvSubmission.VARS_TEMPLATE.keys())] = (
                    valid_subs['praw_inst'].apply(lambda_sub_info))

        # TODO(jcm): Get index matching without column duplication working, 
        # matching objects is slower than matching stringsmmi
        self.cmv_subs = all_subs.merge(valid_subs, on = 'praw_inst')

    def get_sub_info(self, sub_inst):
        '''
        This function retrieves the following information for a single 
        submission:
            - Whether the OP awarded a delta
            - How many deltas the OP awarded
            - Number of top level replies
        '''
        Submission = CmvSubmission(sub_inst, self.praw_agent)
        Submission.parse_root_comments()

        return(Submission.get_series())

    @staticmethod
    def make_output_dir(dir_name):
        '''
        Creates an output directory in current folder if it does not exist
        already and returns the current directory
        '''
        cur_path = os.path.split(os.path.abspath(__file__))[0]
        output_fldr = dir_name
        output_dir = os.path.join(cur_path, output_fldr)
        if not os.access(output_dir, os.F_OK):
            os.makedirs(output_dir)

        return(output_dir)

# Would like to have this inherit from praw's submissions class but with the way
# I'm scraping the data I would have to tinker with a praw's sublisting class 
# and subreddit class.
class CmvSubmission:
    '''
    A class of a /r/changemyview submission
    '''
    VARS_TEMPLATE = {'num_root_comments': 0,
                     'num_user_comments': 0,
                     'OP_gave_delta': False,
                     'num_deltas_from_OP': 0}

    def __init__(self, sub_inst, praw_agent):
        self.praw_agent = praw_agent
        self.submission = sub_inst
        self.author = str(self.submission.author)

        # Important Variables to track
        self.vars = self.VARS_TEMPLATE

    def parse_root_comments(self, comment_tree=None):
        '''
        '''
        if not comment_tree:
            comment_tree = self.submission.comments

        for com in comment_tree:
            if isinstance(com, praw.models.MoreComments):
                self.parse_root_comments(comment_tree.comments())
            elif com.stickied:
                continue # Sticked comments are not replies to view
            else:
                self.vars['num_user_comments'] += 1
                self.vars['num_root_comments'] += 1
                self.parse_replies(com.replies)

    def parse_replies(self, reply_tree):
        '''
        '''
        reply_tree.replace_more(limit=None)

        for reply in reply_tree.list():
            if str(reply.author) == 'DeltaBot':
                self.parse_delta_bot_comment(reply)
            else:
                self.vars['num_user_comments'] += 1

    def parse_delta_bot_comment(self, comment):
        '''
        '''
        text = comment.body
        if 'Confirmed' in text: # If delta awarded
            parent_com = comment.parent()

            # This is probably overkill, but I check to make sure DeltaBot
            # actually responded to a comment and not a submission.
            # (Submission are always by OP, comments are not.)
            if isinstance(parent_com, praw.models.Comment):
                if str(parent_com.author) == self.author:
                    self.vars['OP_gave_delta'] = True
                    self.vars['num_deltas_from_OP'] += 1

    def get_series(self):
        '''
        This function returns a series so this class can update the submissions
        dataframe
        '''
        return(pd.Series(self.vars))


# TODO(jcm): Implement the inheritance from praw's Redditor class, would be a 
# more effective use of OOP
class CmvSubAuthor(Redditor):
    '''
    Class for scraping the history of an author of /r/changemyview
    '''
    VARS_TEMPLATE = {'sub_id': [],
                     'com_id': [],
                     'sub_inst': [],
                     'com_inst': []}

    def __init__(self, user_name, praw_agent):
        '''
        '''
        # self.super().__init__(praw_agent, user_name)
        self.praw_agent = praw_agent
        self.user = self.praw_agent.redditor(user_name)
        self.user_name = user_name

        # Important variables to track
        self.created_utc = self.user.created_utc
        self.history = self.VARS_TEMPLATE

    def get_history_for(self, post_type):
        '''
        '''
        # Get posts
        post_generator = getattr(self, 'post_type')
        posts = post_generator.new(limit=None)

        num_posts_retrieved = 0
        post_prefix = post_type[:3]
        for com in comments:
            num_posts_retrieved += 1
            self.history[post_prefix + '_id'].append(com.id)
            self.history[post_prefix + '_inst'].append(com)

        if num_posts_retrieved == 1000:
            print('1000 {} retrieved exactly,'
                ' may need to find way to retrieve more for {}.'.format(
                    post_type, self.user_name))
        elif num_coms_retrieved > 1000:
            print("{} {} retrieved, don't have to worry about comment limit".format(
                num_posts_retrieved, post_type))

    def get_df_post(self, post_type):
        '''
        This function returns a series so this class can update the authors'
        comments or submissions dataframe in CmvScraperModder.
        '''
        return(pd.DataFrame({post_type_key: value for post_type_key in 
            self.history if post_type_key[:3] == post_type[:3]}))


if __name__ == '__main__':
    SModder = CmvScraperModder()
    # Scraper.update_subs_df(START_BDAY_2016, END_BDAY_2016)