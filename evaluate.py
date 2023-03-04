from totw import totw
from toty import toty
import pandas as pd

class evaluate:

    def __init__(self, gws: list, subs: list=[]):

        """Initialise constructor

        Initialise the evaluate class with the list of players for starting XI
        and the list of substitutes.

        Args:
            gws (list): List of players for starting XI
            subs (list): List of players for substitutes
        """

        self.gws = gws
        self.points_list = self.find_points_list()
        self.subs = subs

    def dataloader(self, gw: int) -> pd.DataFrame:

        """Load a the dataset for a specific gameweek

        This function extracts the name, total points, price, position, 
        team, and unique ID from the gameweek dataset.

        Args:
            gw (int): Gameweek to find points for

        Returns:
            pd.DataFrame: Gameweek Dataframe
        """

        gw = pd.read_csv('gws/gw' + str(gw) + '.csv', encoding='latin1').sort_values(by = 'element').reset_index(drop=True).reindex() # Load gameweek data
        pos_data = pd.read_csv('players_raw.csv', encoding='latin1').rename(columns={'id': 'element'}) # Load position data
        gw = pd.merge(gw, pos_data[['element', 'element_type','team']], on=['element'], how='left') # Extract Important Columns from Position data and Merge dataframes
        return gw[['name','total_points','value','element_type','team','element']] # Return Dataframe with important columns
    
    def find_points_list(self) -> list:

        """Find the list of points for every player in every inputted list we have

        Find the list of points for every player that we have in our inputted
        team.

        Returns:
            list: Points list
        """
        
        full_points_list = []
        for gw in range(1,39):
            df = self.dataloader(gw) 
            points_list = [] # Create variable for current gameweek points list
            for val in self.gws[gw-1]:
                try: # Check if there is a double gameweek
                    df.loc[df['element']==val].values.tolist()[1][1]
                except:
                    x = 0
                else: # Add the number of points for double gameweek
                    points_list.append(df.loc[df['element']==val].values.tolist()[0][1] + df.loc[df['element']==val].values.tolist()[1][1])
                    continue
                try:  # Check if there is a points total at all
                    df.loc[df['element']==val].values.tolist()[0][1]
                except:
                    x = 0
                else: # Add the number of points for a single gameweek
                    points_list.append(df.loc[df['element']==val].values.tolist()[0][1])
            full_points_list.append(points_list) # Append gameweek points list to overall points list   
        return full_points_list
    
    def total_points(self) -> int:

        """Find total number of points for a set of players

        Add the total number of points for the set of players that
        we are trying to evaluate

        Returns:
            int: Number of points
        """

        points = 0
        points += self.find_triple_captain() # Increase points for the Triple Captain Chip
        points += self.find_bench_boost()
        free_hit_chip = self.find_free_chip()# Applies the Free Hit Chip
        self.gws[free_hit_chip[0]-1] = free_hit_chip[1] # Change the gameweek players for the free hit chip
        points -= self.find_deductable(free_hit_chip[0]) # Deduct points for additional transfers made
        self.points_list = self.find_points_list() # Reinitialise the points list - Due to Free Hit Chip played
        for gw in range(1,39):
            gw_points_list = self.points_list[gw-1] # Extract a specific gameweek
            gw_points_list[gw_points_list.index(max(gw_points_list))] = gw_points_list[gw_points_list.index(max(gw_points_list))] * 2 # Multiply highest scoring player points by 2 for captaincy
            points += sum(gw_points_list) # Add gameweek points to total points
        return points
    
    def find_deductable(self, free_hit_gw: int) -> int:

        """Find number of deductable points

        Find the number of non-free transfers made, and hence find the
        number of points that need to be deducted.

        Args:
            free_hit_gw (int): Gameweek that we applied the free hit chip

        Returns:
            int: Deductable points
        """

        changes = []
        sum = 0
        gws_no_free_hit = self.gws.copy()
        gws_no_free_hit[free_hit_gw-1] = gws_no_free_hit[free_hit_gw-2] # Make the free hit gameweek 'invisible' by copying the prior weeks team
        subs_no_free_hit = self.subs.copy()
        subs_no_free_hit[free_hit_gw-1] = subs_no_free_hit[free_hit_gw-2] # Make the free hit gameweek 'invisible' by copying the prior weeks subs
        for val in range(0,36):
            changes.append(len(set(gws_no_free_hit[val] + gws_no_free_hit[val+1] + subs_no_free_hit[val] + subs_no_free_hit[val+1])) - 16)
            sum += len(set(gws_no_free_hit[val] + gws_no_free_hit[val+1] + subs_no_free_hit[val] + subs_no_free_hit[val+1])) - 16
        first_wildcard = changes[0:18].index(max(changes[0:18])) # Find the maximum number of transfers in one gameweek for the first half of the season
        second_wildcard = changes[18:37].index(max(changes[18:37])) # Find the maximum number of transfers in one gameweek for the second half of the season
        print("The First Wilcard Chip will be played in Gameweek", first_wildcard + 2)
        print("The Second Wildcard Chip will be played in Gameweek", second_wildcard + 20)
        sum -= (max(changes[0:18]) + max(changes[18:37])) # Take away the transfer deductables for two gameweeks
        if sum < 0: # If less transfers were used than one per week, there should be no deductables
            return 0
        else: # If more transfers were used than one per week, there are four points deducted per transfer exceeded
            return (4*sum)
    
    def find_free_chip(self) -> list:

        """Find the gameweek for the Free Hit Chip

        Find the gameweek that has the biggest difference between
        team of the week points and our team points and apply the 
        free hit chip

        Returns:
            list: free hit gameweek
        """

        totw_points = []
        for k in range(1,39): # Iterate and find the points of the team of the week for each gameweek
            r = totw(k,True)
            totw_points.append(sum(r.find_points()))
        weekly_points = []
        for k in range(0,38): # Iterate and find the points of the inputted team
            weekly_points.append(sum(self.points_list[k]))
        totw_difference = [a - b for a, b in zip(totw_points, weekly_points)] # Find the difference between the two lists
        free_hit_gameweek = totw_difference.index(max(totw_difference)) + 1 # Find the gameweek of the largest difference
        print("The Free Hit Chip will be played in Gameweek", free_hit_gameweek, "earning an extra", max(totw_difference), "points")
        free_hit = totw(free_hit_gameweek,True)
        return [free_hit_gameweek, free_hit.find_elements()] # Return the free hit team that maximises points
    
    def find_triple_captain(self) -> int:

        """Find the gameweek for the Triple Captain Chip

        Find the player that has scored the highest number of points and
        apply the triple captain chip to them.

        Returns:
            int: Number of points achieved by the triple captain
        """

        high_gameweek = -1
        high_points = -1
        high_index = -1
        for gameweek in self.points_list: # Iterate through each points list and find the maximum points
            index = 0
            for player in gameweek:
                index += 1
                if player > high_points: # If points total larger than current total, replace
                    high_points = player
                    high_index = index
                    high_gameweek = self.points_list.index(gameweek) + 1
        final_index = self.gws[high_gameweek - 1][high_index - 1] # Find the index of the highest scoring player
        df = self.dataloader(38)
        name = df.loc[df['element']==final_index].values.tolist()[0][0] # Find the name of the highest scoring player
        print("The Triple Captain Chip will be played in Gameweek", high_gameweek, "where the player", name, "scored", high_points, "points")
        return high_points

    def find_bench_boost(self) -> int:

        """Find the gameweek for the bench boost chip

        Find the gameweek that has the highest number of points
        from the substitutes and apply the bench boost chip

        Returns:
            int: Points attained by the bench boost chip
        """
        
        if self.subs == []: # Check if there are no subs
            return 0
        subs_points = []
        for k in range(1,39):
            df = self.dataloader(k)
            local_points = 0
            for val in self.subs[k-1]: # For every substitute, find the number of points that they attain every gameweek
                try:
                    df.loc[df['element']==val].values.tolist()[0][1]
                except:
                    local_points += 0
                else:
                    local_points += df.loc[df['element']==val].values.tolist()[0][1]
            subs_points.append(local_points)
        print("The Bench Boost Chip will be played in Gameweek", subs_points.index(max(subs_points)) + 1, "earning an extra", max(subs_points), "points")
        return max(subs_points) # Return the maximum points from a single gameweek.