import pandas as pd
from collections import Counter

class toty:

    # Initialise the constructor, with a range of gameweeks, and whether or not we want to satisfy the constraints
    def __init__(self, gw_i=1, gw_f=38, constraints=False):

        self.gw_i = gw_i
        self.gw_f = gw_f
        self.constraints = constraints

    # Load the data for a certain gameweek
    def dataloader(self, gw):

        gw = pd.read_csv('gws/gw' + str(gw) + '.csv', encoding='latin1').sort_values(by = 'element').reset_index(drop=True).reindex() # Load gameweek data
        pos_data = pd.read_csv('players_raw.csv', encoding='latin1').rename(columns={'id': 'element'}) # Load position data
        gw = pd.merge(gw, pos_data[['element', 'element_type','team']], on=['element'], how='left') # Extract Important Columns from Position data and Merge dataframes
        return gw[['name','total_points','value','element_type','team','element']] # Return Dataframe with important columns

    # Returns the points sum for a chosen team for a chosen gameweek
    def gw_points(self, team, gw):

        gw = self.dataloader(gw)
        sum = 0
        for val in team: # Check if there is a gameweek (or multiple) and add this to the total number of points in the gameweek
            try: # Check if there is a first match, then add the total points to the sum 
                gw.loc[gw['element']==val].values.tolist()[0]
            except:
                sum += 0
            else:
                sum += gw.loc[gw['element']==val].values.tolist()[0][1]
            try: # Check if htere is a second match, then add the total points to the sum 
                gw.loc[gw['element']==val].values.tolist()[1]
            except:
                sum += 0
            else:
                sum += gw.loc[gw['element']==val].values.tolist()[1][1]
            try: # Check if there is a third match, then add the total points to the sum 
                gw.loc[gw['element']==val].values.tolist()[2]
            except:
                sum += 0
            else:
                sum += gw.loc[gw['element']==val].values.tolist()[2][1]
        return sum

    # Define what we are trying to maximize, which is the cumulative gameweek points
    def objective(self, team):

        sum = 0
        for gw in range(self.gw_i, self.gw_f+1): # Add points to the team for each gameweek
            sum += self.gw_points(team, gw)
        return sum

    # Find the top performers for over a give range of gameweeks
    def top_performers(self, num):

        self.points = [0] * 700 # Define points for each player
        for val in range(self.gw_i, self.gw_f+1): # Go through each gameweek and add the points by each player
            df = self.dataloader(val)
            points_df = df['total_points'].tolist() # Extract points column
            elements_df = df['element'].tolist() # Extract elements column
            gw_points = [0] * 700
            i = 0
            for val in elements_df: # Find points for a specific gameweek
                gw_points[val] += points_df[i]
                i += 1
            self.points = [x + y for x, y in zip(self.points, gw_points)] # Add gameweek points to total points for the dataframe
        indices = []
        total_points = self.points.copy()
        for val in range(1,num+1): # For loop to find the players with the top num performers
            max_val = max(total_points)
            indices.append(total_points.index(max_val))
            total_points[total_points.index(max_val)] = -1
        return indices

    # Find the team of the year over a given range of gameweeks
    def find_toty(self):

        df = self.dataloader(38)
        goalkeepers, defenders, midfielders, forwards = [], [], [], []
        players_per_team = [0] * 21 # To keep track of the team constraint
        top_performers = self.top_performers(100)
        for i in range(len(top_performers)):
            row = df.loc[df['element']==top_performers[i]].values.tolist()[0] # Find the row of the top performer
            if players_per_team[row[4]] == 3 and self.constraints == True: # Check if team constraint is satisfied, if we want a constrained team of the year
                continue
            elif row[3] == 1: # Append to goalkeeper list if goalkeeper
                goalkeepers.append(row)
            elif row[3] == 2: # Append to defenders list if defender
                defenders.append(row)
            elif row[3] == 3: # Append to midfielders list if midfielder
                midfielders.append(row)
            elif row[3] == 4: # Append to forwards list if forward
                forwards.append(row)
            players_per_team[row[4]] += 1 # Keep in check the number of players per team
        toty_list = [goalkeepers[0],defenders[0],defenders[1],defenders[2],midfielders[0],midfielders[1],forwards[0]] # Guaranteed to be in the team of the year
        toss_up = [defenders[3],defenders[4],midfielders[2],midfielders[3],midfielders[4],forwards[1],forwards[2]] # Players that may be in the team of the year, depending on who has the highest points
        self.performers = defenders + midfielders + forwards
        toss_up_total_points = []
        for val in toss_up: # Find the total points for all the values in the toss up
            toss_up_total_points.append(self.objective([val[5]]))
        for val in range(0,4): # Add the highest point totals from the toss up to the team of the year list
            toty_list.append(toss_up[toss_up_total_points.index(max(toss_up_total_points))])
            toss_up_total_points[toss_up_total_points.index(max(toss_up_total_points))] = -1
        self.toty_list = sorted(toty_list, key = lambda x:x[3]) # Sort the team of the year by position 
        df_i = self.dataloader(self.gw_i)
        for val in self.toty_list:
            val[1] = self.objective([val[5]]) # Add the total points to the team of the year list
            try: # If there is an initil price, add this price as the purchase price to the team of the year
                df_i.loc[df_i['element']==val[5]].values.tolist()[0]
            except:
                val[2] = val[2]
            else:
                val[2] = df_i.loc[df_i['element']==val[5]].values.tolist()[0][2]
        if self.check_constraints(self.toty_list) == False and self.constraints == True: # If we want to apply constraints and the original team of the year does not satisfy the conditions, optimise the result
            self.constraint_optimising()
            self.substitute_optimising()
        self.toty_list = sorted(self.toty_list, key = lambda x:x[3]) # Sort the team of the year by position 
        return self.toty_list
    
    # If we take into account the constraints, this function finds a team of the year that satisfies the constraints.
    def constraint_optimising(self, changes=1):
        
        potential_toty = []
        for val in self.performers:
            val[1] = self.points[val[5]]
        points_per_price = [val[1] / val[2] for val in self.performers] # Find points per price of potential replacements
        toty_points_per_price = [val[1] / val[2] for val in self.toty_list] # Find points per price of the team of the year
        to_change = toty_points_per_price.index(min(toty_points_per_price)) # Find the team of the year player to change
        if changes == 2: # If needed, find the second team of the year that needs to be changed
            toty_points_per_price[toty_points_per_price.index(min(toty_points_per_price))] = 1000 # Remove the index from minimum points per price
            second_change = toty_points_per_price.index(min(toty_points_per_price)) 
        for val in range(len(points_per_price)): # Replace all the highest performers with the lowest team of the year performer
            toty_edited = self.toty_list.copy()
            toty_edited[to_change] = self.performers[points_per_price.index(max(points_per_price))]
            points_per_price[points_per_price.index(max(points_per_price))] = -1
            if changes == 2: # Replace second lowest team of the year performer
                toty_edited[second_change] = self.performers[points_per_price.index(max(points_per_price))]
            if self.check_constraints(toty_edited): # Check if constraints are satisfied
                potential_toty.append(toty_edited)
        max_potential = -1
        max_pts = -1
        for val in potential_toty: # Find the best team of the year
            if sum([i[1] for i in val for val in potential_toty]) > max_pts:
                max_potential = val
                max_pts = sum([i[1] for i in val for val in potential_toty])
        if max_potential != -1: # Replace the team of the year
            self.toty_list = max_potential
        else: # If there are no potential team of the years, try again with two changes
            self.constraint_optimising(changes=2)
        return

    # Find the names of the team of the year
    def find_names(self):

        return [val[0] for val in self.toty_list]

    # Find the points of the team of the year
    def find_points(self):

        return [val[1] for val in self.toty_list]

    # Find the prices of the team of the year
    def find_prices(self):

        return [val[2] for val in self.toty_list]

    # Find the positions of the team of the year
    def find_positions(self):

        return [val[3] for val in self.toty_list]

    # Find the teams of the team of the year
    def find_teams(self):

        return [val[4] for val in self.toty_list]

    # Find the elements of the team of the year
    def find_elements(self):

        return [val[5] for val in self.toty_list]
    
    # Find the elements of the subsitutes for the team of the year
    def find_subs(self):

        return [val[5] for val in self.subs]

    # Print the team of the year
    def return_toty(self):

        return self.toty_list
    
    def return_subs(self):

        return self.subs
    
    def return_subs_prices(self):

        return [val[2] for val in self.subs]

    # Check if the three constraints are satisfied for the team of the week: Price, Position & Team
    def check_constraints(self, toty_list, alternative_check = False):

        total_value = sum(val[2] for val in toty_list) # Price Constraint: Extract the total value of the team of the year 
        positions = [val[3] for val in toty_list] # Position Constraint: Extract positions of the team of the year
        self.main_teams = [val[4] for val in toty_list] # Team Constraint: Extract the teams of the theam of the year
        self.find_substitutes() # Find optimal substitutes
        if total_value > self.price_constraint: # If price constraint not satisfied, return False
            return False
        if positions.count(1) != 1 or positions.count(2) < 3 or positions.count(2) > 5 or positions.count(3) < 2 or positions.count(3) > 5 or positions.count(4) < 1 or positions.count(4) > 3: # Check Positions Constraint
            return False
        for val in range(1,21): # If number of players from the same team is greater than 3, the team constraint is not satisfied
            if self.main_teams.count(val) > 3:
                return False
        return True

    # Find the optimal subsitutes to help being within the constraints
    def find_substitutes(self):

        total_positions = Counter([1,1,2,2,2,2,2,3,3,3,3,3,4,4,4]) # List of all available positions
        taken_positions = Counter([val[3] for val in self.toty_list]) # List of all taken positions in the team of the year
        remaining_positions = list((total_positions - taken_positions).elements()) # Find the substitute positions that need to be filled 
        df = self.dataloader(self.gw_i).sort_values("value") # Find the prices of all players in the inital gameweek
        self.price_constraint = 1000 # Initial Price Constraint
        self.teams, self.names, self.subs = [], [], []
        for val in remaining_positions: # For every remaining position, find the cheapest substitutes that do not interfere with the team constraints
            for index, row in df.iterrows():
                if row["element_type"] == val and row["name"] not in self.names and (self.main_teams.count(row["team"]) + self.teams.count(row["team"]))< 3:
                    self.price_constraint -= row["value"] # Change the total value of the remaining team
                    self.teams.append(row["team"]) # Make sure team constraint is still satisfied
                    self.names.append(row["name"]) # Make sure not to take the same person for a substitute
                    self.subs.append(row.tolist()) # self.subs holds the list of all the substitutes
                    break
        return self.subs
    
    def substitute_optimising(self):

        extras = int((self.price_constraint - sum(self.find_prices())) / 4)
        df = self.dataloader(self.gw_i)
        temp_subs, self.teams = [], []
        self.main_teams = [val[4] for val in self.toty_list]
        for val in self.subs:
            df_temp = df[df['value'] <= val[2] + extras]
            df_temp = df_temp[df_temp['element_type'] == val[3]]
            for index, row in df_temp.iterrows():
                df_temp.at[index, "total_points"] = self.points[row["element"]]
            df_temp = df_temp.sort_values("total_points", ascending=False)
            for index, row in df_temp.iterrows():
                if row.tolist() not in temp_subs and (self.main_teams.count(row["team"]) + self.teams.count(row["team"])) < 3:
                    temp_subs.append(row.tolist())
                    self.teams.append(row["team"])
                    break
        self.subs = temp_subs