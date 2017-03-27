# Scraper for /r/changemyview data

import praw
import os
import pandas as pd
import re
import numpy as numpy
import time


END_2016 = 1483228799
START_2013 = 1356998400

START_BDAY_2016 = 1461110400
END_BDAY_2016 = 1461196799


class CmvScraper:
    '''
    Class to scrape /r/changemyview for MACS 302 and possibly thesis.
    '''
    def __init__(self):
        '''
        Initializes the class with an instance of the praw.Reddit class.
        '''
        self._praw_agent = praw.Reddit('cmv_scrape', # Site ID
            user_agent = '/u/shugamoe /r/changemyview scraper')
        self._praw_agent.read_only = True # We're just here to look
        self.subreddit = self._praw_agent.subreddit('changemyview')
        self.eg_submission = self._praw_agent.submission('5kgxsz')
        # self.eg_post
        # self.eg_user


    def get_submissions(self, start, end):
        '''
        This function gathers the submission IDs for submissions in 
        /r/changemyview
        '''
        df_col_names = ['id', 'author', 'created_utc']
        sub_df_dict = {col_name: [] for col_name in df_col_names}

        for sub in self.subreddit.submissions(start, end):
            sub_df_dict['author'].append(str(sub.author))
            sub_df_dict['id'].append(str(sub.id))
            sub_df_dict['created_utc'].append(sub.created_utc)

        df = pd.DataFrame(sub_df_dict)
        df['created_utc'] = pd.to_datetime(df['created_utc'], 
            unit = 's')
        self._subs_df = df.set_index('id', drop = False)


    def update_subs_df(self, start, end):
        '''
        This function retrieves following information about submissions:
            - Whether the OP awarded a delta
            - How many deltas the OP awarded
            - Number of top level replies
        '''
        if hasattr(self, '_subs_df'):
            pass
        else:
            self.get_submissions(start, end)

        all_subs = self._subs_df
        valid_subs = all_subs[all_subs['author'] != '[deleted]']

        valid_subs[['num_root_comments', 'num_user_comments',
                    'OP_gave_delta', 'deltas_from_OP']] = (
                    valid_subs['id'].apply(lambda sub_id: 
                        self.get_sub_info(sub_id))
                    )

        print(valid_subs)
        self._subs_df = self._subs_df.merge(valid_subs, on = 'id')


    def get_sub_info(self, sub_id):
        '''
        This function retrieves the following information for a single 
        submission:
            - Whether the OP awarded a delta
            - How many deltas the OP awarded
            - Number of top level replies
        '''
        Submission = CmvSubmission(sub_id, self)
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


class CmvSubmission(CmvScraper):
    '''
    A class of a /r/changemyview submission
    '''
    def __init__(self, sub_id, scraper):
        self._praw_agent = scraper._praw_agent
        self._praw_object = self._praw_agent.submission(sub_id)
        self.author = str(self._praw_object.author)

        # Important Variables to track
        self.num_root_comments = 0
        self.num_user_comments = 0
        self.OP_gave_delta = False
        self.deltas_from_OP = 0


    def parse_root_comments(self, comment_tree = None):
        '''
        '''
        if not comment_tree:
            comment_tree = self._praw_object.comments

        for com in comment_tree:
            if isinstance(com, praw.models.MoreComments):
                self.parse_root_comments(comment_tree.comments())
            elif com.stickied:
                continue # Sticked comments are not replies to view
            else:
                self.num_user_comments += 1
                self.num_root_comments += 1
                self.parse_replies(com.replies)


    def parse_replies(self, reply_tree):
        '''
        '''
        reply_tree.replace_more(limit = None)

        for reply in reply_tree.list():
            if str(reply.author) == 'DeltaBot':
                self.parse_delta_bot_comment(reply)
            else:
                self.num_user_comments += 1

        
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
                    self.OP_gave_delta = True
                    self.deltas_from_OP += 1


    def get_series(self):
        '''
        This function returns a series so this class can update the submissions
        dataframe
        '''
        return(pd.Series([self.num_root_comments, 
                          self.num_user_comments,
                          self.OP_gave_delta,
                          self.deltas_from_OP]))


if __name__ == '__main__':
    Scraper = CmvScraper()
    Scraper.update_subs_df(START_BDAY_2016, END_BDAY_2016)
    # scraper.get_submissions(START_BDAY_2016, END_BDAY_2016)