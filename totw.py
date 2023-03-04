import pandas as pd
from collections import Counter

class totw:

    def __init__(self, gw: int, constraints: bool=False, transfer_dependent: bool=False, prev_totw: list = [], prev_subs: list = []):

        """Initialise the constructor

        Initialise the team of the week constructor, with the current
        gameweek, whether we want to satisfy the constraints, and whether
        we want to take into account transfers.

        Args:
            gw (int): Current gameweek
            constraints (bool): Whether we want to satisfy the constraints
            transfer_dependent (bool): Whether we want to take into account transfers
            prev_totw (list): Previous team of the week
            prev_subs (list): Previous subs
        """

        self.gw = gw
        self.constraints = constraints
        self.transfer_dependent = transfer_dependent
        self.prev_totw = prev_totw
        self.prev_subs = prev_subs
        self.totw = self.find_totw()

    def dataloader(self) -> pd.DataFrame:

        """Load the data for the current gameweek

        This function is called when the constructor is called, and extract the
        name, total points, price, position, team, and unique ID from the 
        gameweek dataset.

        Returns:
            pd.DataFrame: Gameweek dataframe
        """

        gw = pd.read_csv('gws/gw' + str(self.gw) + '.csv', encoding='latin1').sort_values(by = 'element').reset_index(drop=True).reindex() # Load gameweek data
        pos_data = pd.read_csv('players_raw.csv', encoding='latin1').rename(columns={'id': 'element'}) # Load position data
        gw = pd.merge(gw, pos_data[['element', 'element_type','team']], on=['element'], how='left') # Extract Important Columns from Position data and Merge dataframes
        return gw[['name','total_points','value','element_type','team','element']] # Return Dataframe with important columns

    def prev_dataloader(self) -> pd.DataFrame:

        """Load the data for this gameweek and the previous gameweek

        This function loads the previous gameweek in order to take into account
        transfers, and so make optimal transfer decisions on a gameweek-to-gameweek
        basis.

        Returns:
            pd.DataFrame: Gameweek dataframe
        """

        gw = pd.read_csv('gws/gw' + str(self.gw) + '.csv', encoding='latin1').sort_values(by = 'element').reset_index(drop=True).reindex() # Load gameweek data
        pos_data = pd.read_csv('players_raw.csv', encoding='latin1').rename(columns={'id': 'element'}) # Load position data
        gw = pd.merge(gw, pos_data[['element', 'element_type','team']], on=['element'], how='left') # Extract Important Columns from Position data and Merge dataframes
        if self.prev_subs == [] or self.prev_totw == []: # If we do not have the previous week's team of the week or subs, find it
            prev_gameweek = totw(gw=self.gw-1, constraints=self.constraints, transfer_dependent=self.transfer_dependent) # Load the previous gameweek
            self.prev_subs = prev_gameweek.find_subs() # Find the substitutes from the previous week
            self.prev_totw = prev_gameweek.find_elements() # Find the previous team of the week
        effective_extra_points = []
        for k in range(1,len(gw['total_points'])+1): # Add four points for each player on the previous team of the week
            if k in self.prev_totw:
                effective_extra_points.append(4)
            else:
                effective_extra_points.append(0)
        gw['effective_points'] = [x + y for x, y in zip(gw['total_points'], effective_extra_points)] # Find the effective points total
        return gw[['name','total_points','value','element_type','team','element','effective_points']] # Return Dataframe with important columns
    
    def find_totw(self) -> list:

        """Find the team of the week

        This is the main function of the class, where we find the optimal team
        of the week depending on what the user has input, including transfer
        dependencies and constraint adherence.

        Returns:
            list: List of the team of the week
        """

        if self.transfer_dependent == True and self.gw != 1: # If we want to take into account transfers, we find the current dataset and previous one
            df = self.prev_dataloader().sort_values('effective_points', ascending=False) # Sort
        else:
            df = self.dataloader().sort_values('total_points', ascending=False) # Sort
        goalkeepers, defenders, midfielders, forwards = [], [], [], [] # Define list for each position
        players_per_team = [0] * 21
        for index, row in df.iterrows(): # Iterate through rows and append highest points
            if players_per_team[row['team']] == 3 and self.constraints == True: # Check if there is a need to satisfy the team constraint
                continue
            try: # Check if there is a double gameweek
                df.loc[df['element']==row[5]].values.tolist()[1][1]
            except:
                to_add = row.values.tolist()
            else:
                to_add = row.values.tolist()
                to_add[1] += df.loc[df['element']==row[5]].values.tolist()[1][1] # Add the double gameweek points
            if row['element_type'] == 1 and len(goalkeepers) < 1: # Add goalkeepers
                goalkeepers.append(to_add)
            elif row['element_type'] == 2 and len(defenders) < 5: # Add defenders
                defenders.append(to_add)
            elif row['element_type'] == 3 and len(midfielders) < 5: # Add midfielders
                midfielders.append(to_add)
            elif row['element_type'] == 4 and len(forwards) < 3: # Add forwards
                forwards.append(to_add)
            else:
                continue
            players_per_team[row['team']] += 1
        self.totw_list = [goalkeepers[0],defenders[0],defenders[1],defenders[2],midfielders[0],midfielders[1],forwards[0]] # totw_list consists of confirmed values in the team of the week
        toss_up = [defenders[3],defenders[4],midfielders[2],midfielders[3],midfielders[4],forwards[1],forwards[2]] # toss_up consists of players that may be in the team of the week depending on the formation
        toss_up_total_points = []
        for val in toss_up: # Find the total points for all the values in the toss up
            toss_up_total_points.append(val[1])
        for val in range(0,4): # Add the highest point totals from the toss up to the team of the year list
            self.totw_list.append(toss_up[toss_up_total_points.index(max(toss_up_total_points))])
            toss_up_total_points[toss_up_total_points.index(max(toss_up_total_points))] = -1
        while self.constraints == True and self.check_constraints() == False: # Satisfy the price constraint if needed
            next_best = toss_up[toss_up_total_points.index(max(toss_up_total_points))]
            for val in self.totw_list:
                if val[3] == next_best[3] and val[2] > next_best[2]: # Swap if possible
                    self.totw_list[self.totw_list.index(val)] = next_best
                    break
            toss_up_total_points[toss_up_total_points.index(max(toss_up_total_points))] = -1
        self.totw_list = sorted(self.totw_list, key = lambda x:x[3]) # Sort the list
        return self.totw_list

    def find_elements(self) -> list:

        """Find the unique IDs of the players for the team of the week.

        Returns:
            list: Unique IDs of the players for the team of the week
        """

        return [val[5] for val in self.totw]

    def find_names(self) -> list:

        """Find the names of the players for the team of the week.

        Returns:
            list: Names of the players for the team of the week
        """

        return [val[0] for val in self.totw]
    
    def find_points(self) -> list:

        """Find the points of the players for the team of the week.

        Returns:
            list: Points of the players for the team of the week
        """

        return [val[1] for val in self.totw]


    def find_prices(self) -> list:

        """Find the prices of the players for the team of the week.

        Returns:
            list: Prices of the players for the team of the week
        """

        return [val[2] for val in self.totw]
    
    def find_subs(self) -> list:

        """Find the substitutes of the players for the team of the week.

        Returns:
            list: Unique IDs of the substitutes of the team of the week
        """

        return [val[5] for val in self.subs]
    
    def return_subs(self) -> list:

        """Find the substitutes of the team of the week.
        
        Returns:
            list: The substitutes of the team of the week
        """

        return self.subs
    
    def return_subs_prices(self) -> list:

        """Find the prices of the substitutes of the team of the week.

        Returns:
            list: The prices of substitutes of the team of the week
        """

        return [val[2] for val in self.subs]
    
    def totw_cumulative(self) -> int:

        """Find the cumulative number of points from the team of the weeks up to now.

        Returns:
            int: Cumulative number of points achieved by the team of the week up to now
        """

        return sum(sum(val[1] for val in totw(k,self.constraints).totw) for k in range(1, self.gw+1))

    def check_constraints(self) -> bool:

        """Check if the team satisfies all of the constraints

        Check if the team of the week satisfies all of the constraints. First
        check if the team constraint is satisfied, then check if the price
        constraint is satisfied. The position satisfied is satisfied regardless.

        Returns:
            bool: True if team satisfies all constraints. Else False
        """

        total_value = sum(val[2] for val in self.totw_list)
        self.main_teams = [val[4] for val in self.totw_list]
        self.find_substitutes()
        for val in range(1,21):
            if self.main_teams.count(val) > 3: # Check team constraint
                return False
        if total_value > self.price_constraint: # Check price constraint
            return False
        else:
            return True

    def find_substitutes(self) -> list:

        """Find the optimal subsitutes to help being within the constraints

        Find the substitute positions available, and find the cheapest possible
        players to fit into the substitute constraints

        Returns:
            list: Four substitute players
        """

        total_positions = Counter([1,1,2,2,2,2,2,3,3,3,3,3,4,4,4]) # List of all available positions
        taken_positions = Counter([val[3] for val in self.totw_list]) # List of all taken positions in the team of the year
        remaining_positions = list((total_positions - taken_positions).elements()) # Find the substitute positions that need to be filled 
        df = self.dataloader().sort_values("value") # Find the prices of all players in the inital gameweek
        self.price_constraint = 1000 # Initial Price Constraint
        self.teams, self.names, self.subs = [], [], []
        if self.transfer_dependent == True and self.gw != 1: # If dependent on transfers, check the last gameweeks substitutes
            for val in self.prev_subs:
                try: # Find the previous subsitute, if possible
                    df[df['element'] == val].values.tolist()[0]
                except:
                    continue
                else:
                    prev_row = df[df['element'] == val].values.tolist()[0] # Check if the constraints are satisfied
                if (prev_row[3] in remaining_positions) and (prev_row[0] not in self.names) and ((self.main_teams.count(prev_row[4]) + self.teams.count(prev_row[4])) < 3):
                        self.price_constraint -= prev_row[2]
                        self.teams.append(prev_row[5])
                        self.names.append(prev_row[0])
                        self.subs.append(prev_row) # Append same substitute
                        remaining_positions[remaining_positions.index(prev_row[3])] = -1 # Remove from remaining positions
        for val in remaining_positions: # For every remaining position, find the cheapest substitutes that do not interfere with the team constraints
            if val == -1:
                continue
            for index, row in df.iterrows(): # Iterate through the cheapest possible subs
                if row["element_type"] == val and row["name"] not in self.names and (self.main_teams.count(row["team"]) + self.teams.count(row["team"]))< 3:
                    self.price_constraint -= row["value"]
                    self.teams.append(row["team"])
                    self.names.append(row["name"])
                    self.subs.append(row.tolist())
                    break
        return self.subs
