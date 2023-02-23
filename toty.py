import pandas as pd
import random
from collections import Counter

class toty:

    def __init__(self, gw_i=1, gw_f=38, constraints=False):

        self.gw_i = gw_i
        self.gw_f = gw_f
        self.constraints = constraints

    # Load the data for a certain gameweek
    def dataloader(self, gw):

        gw = 'gw' + str(gw)
        url = 'gws/' + gw + '.csv'
        gw = pd.read_csv(url, encoding='latin1') # Load gameweek data
        pos_data = pd.read_csv('C:/Users/Adnan/Downloads/players_raw.csv', encoding='latin1') # Load position data
        gw = gw.sort_values(by = 'element').reset_index(drop=True).reindex()
        pos_data = pos_data.rename(columns={'id': 'element'})
        pos_data_team_element = pos_data[['element', 'element_type','team']] # Extract position and team data
        gw = pd.merge(gw, pos_data_team_element, on=['element'], how='left') # Merge dataframes
        gw = gw[['name','total_points','value','element_type','team','element']]
        return gw

    # Returns the points sum for a chosen team for a chosen gameweek
    def gw_points(self, team, gw):

        gw = self.dataloader(gw)
        sum = 0
        for val in team:
            try:
                gw.loc[gw['element']==val].values.tolist()[0]
            except:
                sum += 0
            else:
                sum += gw.loc[gw['element']==val].values.tolist()[0][1]
            try:
                gw.loc[gw['element']==val].values.tolist()[1]
            except:
                sum += 0
            else:
                sum += gw.loc[gw['element']==val].values.tolist()[1][1]
            try:
                gw.loc[gw['element']==val].values.tolist()[2]
            except:
                sum += 0
            else:
                sum += gw.loc[gw['element']==val].values.tolist()[2][1]
        return sum

    # Define what we are trying to maximize, which is the cumulative gameweek points
    def objective(self, team):

        sum = 0
        for gw in range(self.gw_i, self.gw_f+1):
            sum += self.gw_points(team, gw)
        return sum

    # Find the top performers for over a give range of gameweeks
    def top_performers(self, num):

        self.points = [0] * 700
        for val in range(self.gw_i, self.gw_f+1): # Go through each gameweek and add the points by each player
            df = self.dataloader(val)
            points_df = df['total_points'].tolist()
            elements_df = df['element'].tolist()
            gw_points = [0] * 700
            i = 0
            for val in elements_df:
                gw_points[val] += points_df[i]
                i += 1
            self.points = [x + y for x, y in zip(self.points, gw_points)]
        indices = []
        local_points = self.points.copy()
        for val in range(1,num+1): # For loop to find the players with the top num performers
            max_val = max(local_points)
            indices.append(local_points.index(max_val))
            local_points[local_points.index(max_val)] = -1
        return indices

    # Find the team of the year over a given range of gameweeks
    def find_toty(self):

        df = self.dataloader(38)
        goalkeepers, defenders, midfielders, forwards = [], [], [], []
        players_per_team = [0] * 21
        top_performers = self.top_performers(250)
        for i in range(len(top_performers)):
            row = df.loc[df['element']==top_performers[i]].values.tolist()[0]
            if players_per_team[row[4]] == 3 and self.constraints == True:
                continue
            if row[3] == 1:
                goalkeepers.append(row)
                players_per_team[row[4]] += 1
                top_performers[i] = -1
            elif row[3] == 2:
                defenders.append(row)
                players_per_team[row[4]] += 1
                top_performers[i] = -1
            elif row[3] == 3:
                midfielders.append(row)
                players_per_team[row[4]] += 1
                top_performers[i] = -1
            elif row[3] == 4:
                forwards.append(row)
                players_per_team[row[4]] += 1
                top_performers[i] = -1
        toty_list = [goalkeepers[0],defenders[0],defenders[1],defenders[2],midfielders[0],midfielders[1],forwards[0]]
        self.toss_up = [defenders[3],defenders[4],midfielders[2],midfielders[3],midfielders[4],forwards[1],forwards[2]]
        toss_up_total_points = []
        for val in self.toss_up:
            toss_up_total_points.append(self.objective([val[5]]))
        for val in range(0,4):
            toty_list.append(self.toss_up[toss_up_total_points.index(max(toss_up_total_points))])
            toss_up_total_points[toss_up_total_points.index(max(toss_up_total_points))] = -1
        self.toty_list = sorted(toty_list, key = lambda x:x[3])
        df_i = self.dataloader(self.gw_i)
        for val in self.toty_list:
            val[1] = self.objective([val[5]])
            try:
                df_i.loc[df_i['element']==val[5]].values.tolist()[0]
            except:
                val[2] = val[2]
            else:
                val[2] = df_i.loc[df_i['element']==val[5]].values.tolist()[0][2]
        if self.check_constraints() == False and self.constraints == True:
            self.constraint_optimising_2(top_performers, df)
        self.toty_list = sorted(self.toty_list, key = lambda x:x[3])
        return self.toty_list
    
    def constraint_optimising_2(self, top_performers, df):

        checked_elements = []
        potential_toty = []
        self.price_diff = []
        self.points_diff = []
        local_check = self.toty_list.copy()
        for val in self.toss_up:
            val[1] = self.points[val[5]]
            local_check = self.toty_list.copy()
            if val[5] in [i[5] for i in self.toty_list]:
                continue
            checked_elements.append(val[5])
            self.local_price_diff, self.local_points_diff = [], []
            for k in range(len(local_check)):
                local_check = self.toty_list.copy()
                local_check[k] = val
                if self.check_constraints_local(local_check):
                    potential_toty.append(local_check)
            self.price_diff.append(self.local_price_diff)
            self.points_diff.append(self.local_points_diff)
        max_potential = -1
        max_pts = -1
        for val in potential_toty:
            if sum([i[1] for i in val]) > max_pts:
                max_potential = val
        self.toty_list = max_potential
        return


    def constraint_optimising(self, top_performers, df):
        pos = self.find_positions()
        while not self.check_constraints():
            randint = random.randint(0,99)
            random_swap = top_performers[randint]
            if random_swap == -1:
                continue
            else:
                top_performers[randint] = -1
            row = df.loc[df['element']==random_swap].values.tolist()[0]
            if row[3] == 1:
                if self.toty_list[0][2] < row[2]:
                    continue
                self.toty_list[0] = row
            elif row[3] == 2:
                randomint = random.randint(pos.index(2),pos.index(3)-1)
                if self.toty_list[randomint][2] < row[2]:
                    continue
                self.toty_list[randomint] = row
            elif row[3] == 3:
                randomint = random.randint(pos.index(3),pos.index(4)-1)
                if self.toty_list[randomint][2] < row[2]:
                    continue
                self.toty_list[randomint] = row
            elif row[3] == 4:
                randomint = random.randint(pos.index(4),10)
                if self.toty_list[randomint][2] < row[2]:
                    continue
                self.toty_list[randomint] = row
        return self.toty_list


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

        return [val[5] for val in self.toty_list]# + [val for val in self.element]
    
    def extract_subs_elements(self):

        return [val[5] for val in self.subs]

    # Print the team of the year
    def print_toty(self):

        print(self.toty_list)
        return self.toty_list

    # Print the total points of the team of the year
    def print_points(self):

        print(sum(self.find_points()))
        return sum(self.find_points())

    # Print to the total cost of the team of the year
    def print_value(self):

        print(sum(self.find_prices()))
        return sum(self.find_prices())

    # Check if the three constraints are satisfied for the team of the week: Price, Team & Position
    def check_constraints_local(self, local_check):

        positions = [val[3] for val in local_check]
        total_value = sum(val[2] for val in local_check)
        self.main_teams = [val[4] for val in local_check]
        self.find_subs()
        team_boolean = True
        position_boolean = True
        self.local_price_diff.append(total_value - sum(self.find_prices()))
        self.local_points_diff.append(sum(val[1] for val in local_check) - sum(self.find_points()))
        if positions.count(1) != 1 or positions.count(2) < 3 or positions.count(2) > 5 or positions.count(3) < 2 or positions.count(3) > 5 or positions.count(4) < 1 or positions.count(4) > 3: # Check Positions Constraint
            position_boolean = False
        for val in range(1,21): # If number of players from the same team is greater than 3, the team constraint is not satisfied
            if self.main_teams.count(val) > 3:
                team_boolean = False
        if total_value > self.price_constraint or team_boolean == False or position_boolean == False: # If any of the constraints are not satisfied, return false. Else, return true.
            return False
        else:
            return True
        
    def check_constraints(self):

        positions = [val[3] for val in self.toty_list]
        total_value = sum(val[2] for val in self.toty_list)
        self.main_teams = [val[4] for val in self.toty_list]
        self.find_subs()
        team_boolean = True
        position_boolean = True
        if positions.count(1) != 1 or positions.count(2) < 3 or positions.count(2) > 5 or positions.count(3) < 2 or positions.count(3) > 5 or positions.count(4) < 1 or positions.count(4) > 3: # Check Positions Constraint
            position_boolean = False
        for val in range(1,21): # If number of players from the same team is greater than 3, the team constraint is not satisfied
            if self.main_teams.count(val) > 3:
                team_boolean = False
        if total_value > self.price_constraint or team_boolean == False or position_boolean == False: # If any of the constraints are not satisfied, return false. Else, return true.
            return False
        else:
            return True

    # Find the optimal subsitutes to help being within the constraints
    def find_subs(self):

        total_positions = Counter([1,1,2,2,2,2,2,3,3,3,3,3,4,4,4])
        taken_positions = Counter([val[3] for val in self.toty_list])
        remaining_positions = list((total_positions - taken_positions).elements()) # Find the substitute positions that need to be filled 
        df = self.dataloader(self.gw_i).sort_values("value")
        #df = df.sample(frac=1) # Add Randomness
        self.price_constraint = 1000
        self.teams, self.names, self.element, self.subs = [], [], [], []
        for val in remaining_positions: # For every remaining position, find the cheapest substitutes that do not interfere with the team constraints
            for index, row in df.iterrows():
                if row["element_type"] == val and row["name"] not in self.names and (self.main_teams.count(row["team"]) + self.teams.count(row["team"]))< 3:
                    self.price_constraint -= row["value"]
                    self.teams.append(row["team"])
                    self.names.append(row["name"])
                    self.element.append(row["element"])
                    self.subs.append(row.tolist())
                    break
        return self.subs

if __name__ == "__main__":

    r = toty(1,38,True)
    #s = toty(20,38,True)
    r.find_toty()
    #s.find_toty()
    print(r.find_elements())
    #print(s.find_elements())
    #print(r.extract_subs_elements())
    #print(s.extract_subs_elements())
    #print(sum(r.find_points()) + sum(s.find_points()))
    print(r.find_points())
    print(r.find_names())
    print((r.find_prices()))
    print(sum(r.find_points()))