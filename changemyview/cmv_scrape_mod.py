# Scraper for /r/changemyview data

import praw
from prawcore.exceptions import Forbidden
import os
import pandas as pd
import re
import numpy as numpy
import time
import numpy as np
import pdb
import pickle

END_2016 = 1483228799
START_2013 = 1356998400

START_BDAY_2016 = 1461110400
END_BDAY_2016 = 1461196799


class CMVScraperModder:
    '''
    Class to scrape /r/changemyview for MACS 302 and possibly thesis.
    '''
    def __init__(self, start, end):
        '''
        Initializes the class with an instance of the praw.Reddit class.
        '''
        # PRAW objects
        self.praw_agent = praw.Reddit('cmv_scrape', # Site ID
            user_agent = '/u/shugamoe /r/changemyview scraper')
        self.subreddit = self.praw_agent.subreddit('changemyview')

        self.praw_agent.read_only = True # We're just here to look

        # Start and end dates of interest
        self.date_start = start
        self.date_end = end

        # Example instances to to tinker with
        self.eg_submission = self.praw_agent.submission('5kgxsz')
        self.eg_comment = self.praw_agent.comment('cr2jp5a')
        self.eg_user = self.praw_agent.redditor('RocketCity1234')

    def get_submissions(self):
        '''
        This function gathers the submission IDs for submissions in 
        /r/changemyview
        '''
        init_col_names = ['id', 'author', 'sub_inst']
        sub_df_dict = {col_name: [] for col_name in init_col_names}

        subs_gathered = 0
        for sub in self.subreddit.submissions(self.date_start, 
                self.date_end):
            subs_gathered += 1
            sub_df_dict['author'].append(str(sub.author))
            sub_df_dict['id'].append(sub.id)
            sub_df_dict['sub_inst'].append(sub)

        print('{} submissions gathered'.format(subs_gathered))
        df = pd.DataFrame(sub_df_dict)
        self.cmv_subs = df.set_index('id', drop = False)

    def update_cmv_submissions(self):
        '''
        This function retrieves following information about submissions:
            - Whether the OP awarded a delta
            - How many deltas the OP awarded
            - Number of top level replies
        '''
        if hasattr(self, 'cmv_subs'):
            pass
        else:
            self.get_submissions()

        all_subs = self.cmv_subs
        valid_subs = all_subs[all_subs['author'] != '[deleted]'][['sub_inst']]

        valid_subs[list(CMVSubmission.STATS_TEMPLATE.keys())] = (
                valid_subs['sub_inst'].apply(lambda sub_inst:
                    CMVSubmission(sub_inst).get_stats_series()))

        # TODO(jcm): Get index matching without column duplication working, 
        # matching objects is slower than matching strings
        self.cmv_subs = all_subs.merge(valid_subs, on='sub_inst')

    def _get_sub_info(self, sub_inst):
        '''
        This function retrieves the following information for a single 
        submission:
            - Whether the OP awarded a delta
            - How many deltas the OP awarded
            - Number of top level replies
        '''
        Submission = CMVSubmission(sub_inst)
        Submission.parse_root_comments()

        return(Submission.get_stats_series())
    
    def get_author_histories(self):
        '''
        '''
        if hasattr(self, 'cmv_subs'):
            pass
        else:
            self.get_submissions()
        
        get_auth_hist_vrized = np.vectorize(self._get_author_history,
                otypes='?') # otypes kwarg to avoid double appplying func
        get_auth_hist_vrized(self.cmv_subs['author'].unique())
        
        
        

    def _get_author_history(self, author):
        '''
        '''
        SubAuthor = CMVSubAuthor(self.praw_agent.redditor(author))
        try:
            SubAuthor.get_history_for('comments')
            SubAuthor.get_history_for('submissions')
        except Forbidden:
            print('{} was suspended'.format(author))
            return(None)
        
        if hasattr(self, 'cmv_author_coms'):
            self.cmv_author_coms= self.cmv_author_coms.append(
                    SubAuthor.get_post_df('comments'))
        else:
            self.cmv_author_coms = SubAuthor.get_post_df('comments')

        if hasattr(self, 'cmv_author_subs'):
            self.cmv_author_subs = self.cmv_author_subs.append(
                    SubAuthor.get_post_df('submissions'))
        else:
            self.cmv_author_subs = SubAuthor.get_post_df('submissions')

    def update_author_history(self):
        '''
        '''
        if hasattr(self, 'cmv_author_coms'):
            pass
        else:
            self.get_author_histories()
        # Update Submissions
        sub_inst_series = self.cmv_author_subs[['sub_inst']]

        sub_inst_series[list(CMVAuthSubmission.STATS_TEMPLATE.keys())] = (
                sub_inst_series['sub_inst'].apply(
                    lambda sub_inst: CMVAuthSubmission(sub_inst).get_stats_series()
                ))
        self.cmv_author_subs = self.cmv_author_subs.merge(sub_inst_series, on=
                'sub_inst')
        
        # Update Comments
        # com_inst_series = self.cmv_author_coms[['com_inst']]
        # com_inst_series[list(CMV


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
class CMVSubmission:
    '''
    A class of a /r/changemyview submission
    '''
    STATS_TEMPLATE = {'num_root_comments': 0,
                     'num_user_comments': 0,
                     'OP_gave_delta': False,
                     'num_deltas_from_OP': 0}

    def __init__(self, sub_inst):
        self.submission = sub_inst
        self.author = str(self.submission.author)

        # Important Variables to track
        self.stats = self.STATS_TEMPLATE

        self.parsed = False 

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
                self.stats['num_user_comments'] += 1
                self.stats['num_root_comments'] += 1
                self.parse_replies(com.replies)

        self.parsed = True

    def parse_replies(self, reply_tree):
        '''
        '''
        reply_tree.replace_more(limit=None)

        for reply in reply_tree.list():
            if str(reply.author) == 'DeltaBot':
                self.parse_delta_bot_comment(reply)
            else:
                self.stats['num_user_comments'] += 1

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
                    self.stats['OP_gave_delta'] = True
                    self.stats['num_deltas_from_OP'] += 1

    def get_stats_series(self):
        '''
        This function returns a series so this class can update the submissions
        dataframe
        '''
        if not self.parsed:
            self.parse_root_comments()
        return(pd.Series(self.stats))


# TODO(jcm): Implement the inheritance from praw's Redditor class, would be a 
# more effective use of OOP
class CMVSubAuthor:
    '''
    Class for scraping the history of an author of /r/changemyview
    '''
    STATS_TEMPLATE = {'sub_id': [],
                     'com_id': [],
                     'sub_inst': [],
                     'com_inst': []}

    def __init__(self, redditor_inst):
        '''
        '''
        self.user = redditor_inst
        self.user_name = str(redditor_inst.name)

        # Important variables to track
        self.history = self.STATS_TEMPLATE

    def get_history_for(self, post_type):
        '''
        '''
        # Get posts
        post_generator = getattr(self.user, post_type)
        posts = post_generator.new(limit=None)

        posts_retrieved = 0
        post_prefix = post_type[:3]
        for post in posts:
            posts_retrieved += 1
            self.history[post_prefix + '_id'].append(post.id)
            self.history[post_prefix + '_inst'].append(post)

        # pdb.set_trace()
        if posts_retrieved == 1000:
            print('1000 {} retrieved exactly,'
                ' attempting to retrive more for {}.'.format(
                    post_type, self.user_name))
            self.get_more_history_for(post_prefix, post_type,
                    post_generator)
        elif posts_retrieved > 1000:
            print("{} {} retrieved, don't have to worry about comment limit".format(
                posts_retrieved, post_type))
        else:
            print("{} {} retrieved for {}".format(posts_retrieved,
                post_type, self.user_name))

    def get_more_history_for(self, post_prefix, post_type, post_generator):
        '''
        '''
        con_posts = post_generator.controversial(limit=None)
        hot_posts = post_generator.hot(limit=None)
        top_posts = post_generator.top(limit=None)
        
        new_posts_found, same_posts_found = 0, 0
        for post_types in zip(con_posts, hot_posts, top_posts):
            for post in post_types:
                if post not in self.history[post_prefix + '_id']:
                    new_posts_found += 1
                    self.history[post_prefix + '_id'].append(post.id)
                    self.history[post_prefix + '_inst'].append(post)
                else:
                    same_posts_found += 1
        
        if new_posts_found == 3000:
            print("Maximum number (3000) of new [] found".format(post_type))
        else:
            print("{} new and {} same {} found".format(new_posts_found,
                same_posts_found, post_type))

    def get_post_df(self, post_type):
        '''
        This function returns a series so this class can update the authors'
        comments or submissions dataframe in CMVScraperModder.
        '''
        attribution_dict = {post_type_key: value for post_type_key, value in
                self.history.items() if post_type[:3] == 
                post_type_key[:3]}
        attribution_dict.update({'author': self.user_name})
        return(pd.DataFrame(attribution_dict))

# TODO(jcm): Make CMVSubmission inherit from CMVAuthSubmission
class CMVAuthSubmission:
    '''
    '''
    STATS_TEMPLATE = {'created_utc': None,
                     'score': None,
                     'subreddit': None,
                     'content': None}
    def __init__(self, submission_inst):
        '''
        '''
        self.submission = submission_inst
        self.stats = self.STATS_TEMPLATE
        self.parsed = True

        # Stats that can be gathered right off the bat
        self.stats['created_utc'] = self.submission.created_utc
        self.stats['score'] = self.submission.score
        self.stats['subreddit'] = self.submission.subreddit_name_prefixed
        self.stats['content'] = self.submission.selftext

    def get_stats_series(self):
        '''
        '''
        return(pd.Series(self.stats))

# STATS_TEMPLATE for date, score, subreddit. Could probably include a general
# method to update that dictionary in self.stats as well. Would also reduce
# redundancy in having 2 get_stats_series.
class CMVAuthComment:
    '''
    '''
    STATS_TEMPLATE = {'created_utc': None,
                      'score': None,
                      'subreddit': None,
                      'content': None}

    def __init__(self, comment_inst):
        '''
        '''
        self.comment = comment_inst
        self.stats = self.STATS_TEMPLATE
        self.parsed = True

        # Stats that can be gathered right away
        self.stats['created_utc'] = self.comment.created_utc 
        self.stats['score'] = self.comment.score
        self.stats['subreddit'] = (self.comment.
                submission.subreddit_name_prefixed)
        self.stats['content'] = self.comment.body

    def get_stats_series(self):
        '''
        '''
        return(pd.Series(self.stats))

    
if __name__ == '__main__':
    SModder = CMVScraperModder(START_BDAY_2016, END_BDAY_2016)

    #uSModder.update_cmv_submissions()
    # SModder.update_author_submissions()
    # with open('test.pkl', 'wb') as output:
     #    pickle.dump(SModder, output)
