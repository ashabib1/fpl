import pandas as pd
from collections import Counter

class totw:

    def __init__(self, gw, constraints=False, transfer_dependent=False):

        self.gw = gw
        self.constraints = constraints
        self.transfer_dependent = transfer_dependent
        self.totw = self.find_totw()

    # Load the data for the gameweek
    def dataloader(self):

        gw = pd.read_csv('gws/gw' + str(self.gw) + '.csv', encoding='latin1').sort_values(by = 'element').reset_index(drop=True).reindex() # Load gameweek data
        pos_data = pd.read_csv('players_raw.csv', encoding='latin1').rename(columns={'id': 'element'}) # Load position data
        gw = pd.merge(gw, pos_data[['element', 'element_type','team']], on=['element'], how='left') # Extract Important Columns from Position data and Merge dataframes
        return gw[['name','total_points','value','element_type','team','element']] # Return Dataframe with important columns

    def prev_dataloader(self):

        gw = pd.read_csv('gws/gw' + str(self.gw) + '.csv', encoding='latin1').sort_values(by = 'element').reset_index(drop=True).reindex() # Load gameweek data
        pos_data = pd.read_csv('players_raw.csv', encoding='latin1').rename(columns={'id': 'element'}) # Load position data
        gw = pd.merge(gw, pos_data[['element', 'element_type','team']], on=['element'], how='left') # Extract Important Columns from Position data and Merge dataframes
        prev_gameweek = totw(gw=self.gw-1, constraints=self.constraints, transfer_dependent=self.transfer_dependent)
        self.prev_subs = prev_gameweek.extract_subs()
        prev_totw = prev_gameweek.extract_indices()
        list2 = []
        for k in range(1,len(gw['total_points'])+1):
            if k in prev_totw:
                list2.append(4)
            else:
                list2.append(0)
        gw['effective_points'] = [x + y for x, y in zip(gw['total_points'], list2)]
        return gw[['name','total_points','value','element_type','team','element','effective_points']] # Return Dataframe with important columns
    
    # Find the team of the week
    def find_totw(self):

        if self.transfer_dependent == True and self.gw != 1:
            df = self.prev_dataloader().sort_values('effective_points', ascending=False) # Sort
        else:
            df = self.dataloader().sort_values('total_points', ascending=False) # Sort
        goalkeepers, defenders, midfielders, forwards = [], [], [], [] # Define list for each position
        players_per_team = [0] * 21
        for index, row in df.iterrows(): # Iterate through rows and append highest points
            if players_per_team[row['team']] == 3 and self.constraints == True: # Check if there is a need to satisfy the team constraint
                continue
            if row['element_type'] == 1 and len(goalkeepers) < 1:
                try:
                    df.loc[df['element']==row[5]].values.tolist()[1][1]
                except:
                    goalkeepers.append(row.values.tolist())
                else:
                    to_add = row.values.tolist()
                    to_add[1] += df.loc[df['element']==row[5]].values.tolist()[1][1]
                    goalkeepers.append(to_add)
                players_per_team[row['team']] += 1
            if row['element_type'] == 2 and len(defenders) < 5:
                try:
                    df.loc[df['element']==row[5]].values.tolist()[1][1]
                except:
                    defenders.append(row.values.tolist())
                else:
                    to_add = row.values.tolist()
                    to_add[1] += df.loc[df['element']==row[5]].values.tolist()[1][1]
                    defenders.append(to_add)
                players_per_team[row['team']] += 1
            if row['element_type'] == 3 and len(midfielders) < 5:
                try:
                    df.loc[df['element']==row[5]].values.tolist()[1][1]
                except:
                    midfielders.append(row.values.tolist())
                else:
                    to_add = row.values.tolist()
                    to_add[1] += df.loc[df['element']==row[5]].values.tolist()[1][1]
                    midfielders.append(to_add)
                players_per_team[row['team']] += 1
            if row['element_type'] == 4 and len(forwards) < 3:
                try:
                    df.loc[df['element']==row[5]].values.tolist()[1][1]
                except:
                    forwards.append(row.values.tolist())
                else:
                    to_add = row.values.tolist()
                    to_add[1] += df.loc[df['element']==row[5]].values.tolist()[1][1]
                    forwards.append(to_add)
                players_per_team[row['team']] += 1
        self.totw_list = [goalkeepers[0],defenders[0],defenders[1],defenders[2],midfielders[0],midfielders[1],forwards[0]] # totw_list consists of confirmed values in the team of the week
        toss_up = [defenders[3],defenders[4],midfielders[2],midfielders[3],midfielders[4],forwards[1],forwards[2]] # toss_up consists of players that may be in the team of the week depending on the formation
        toss_up_total_points = []
        for val in toss_up:
            toss_up_total_points.append(val[1])
        for val in range(0,4):
            self.totw_list.append(toss_up[toss_up_total_points.index(max(toss_up_total_points))])
            toss_up_total_points[toss_up_total_points.index(max(toss_up_total_points))] = -1
        while self.constraints == True and self.check_constraints() == False: # Check the value constraint
            t = toss_up[toss_up_total_points.index(max(toss_up_total_points))]
            for val in self.totw_list:
                if val[3] == t[3] and val[2] > t[2]:
                    self.totw_list[self.totw_list.index(val)] = t
                    break
            toss_up_total_points[toss_up_total_points.index(max(toss_up_total_points))] = -1
        self.totw_list = sorted(self.totw_list, key = lambda x:x[3]) # Sort the list
        return self.totw_list

    # Find the unique IDs of the players for the team of the week
    def extract_indices(self):

        return [val[5] for val in self.totw]

    # Find the names of the players for the team of the week
    def extract_names(self):

        return [val[0] for val in self.totw]
    
    def extract_points(self):

        return [val[1] for val in self.totw]
    
    def extract_prices(self):

        return [val[2] for val in self.totw]
    
    def extract_subs(self):

        return [val[5] for val in self.subs]
    
    # Find the cumulative number of points from the team of the weeks up to now
    def totw_cumulative(self):

        return sum(sum(val[1] for val in totw(k,self.constraints).totw) for k in range(1, self.gw+1))

    # Check if the three constraints are satisfied for the team of the week: Price, Team & Position
    def check_constraints(self):

        total_value = sum(val[2] for val in self.totw_list)
        self.main_teams = [val[4] for val in self.totw_list]
        self.find_subs()
        for val in range(1,21):
            if self.main_teams.count(val) > 3:
                return False
        if total_value > self.price_constraint: # If any of the constraints are not satisfied, return false. Else, return true.
            return False
        else:
            return True

    # Find the optimal subsitutes to help being within the constraints
    def find_subs(self):

        total_positions = Counter([1,1,2,2,2,2,2,3,3,3,3,3,4,4,4])
        taken_positions = Counter([val[3] for val in self.totw_list])
        remaining_positions = list((total_positions - taken_positions).elements()) # Find the substitute positions that need to be filled 
        df = self.dataloader().sort_values("value")
        self.price_constraint = 1000
        self.teams, self.names, self.subs = [], [], []
        if self.transfer_dependent == True and self.gw != 1:
            for val in self.prev_subs:
                try:
                    df[df['element'] == val].values.tolist()[0]
                except:
                    continue
                else:
                    prev_row = df[df['element'] == val].values.tolist()[0]
                if (prev_row[3] in remaining_positions) and (prev_row[0] not in self.names) and ((self.main_teams.count(prev_row[4]) + self.teams.count(prev_row[4])) < 3):
                        self.price_constraint -= prev_row[2]
                        self.teams.append(prev_row[5])
                        self.names.append(prev_row[0])
                        self.subs.append(prev_row)
                        remaining_positions[remaining_positions.index(prev_row[3])] = -1
        for val in remaining_positions: # For every remaining position, find the cheapest substitutes that do not interfere with the team constraints
            if val == -1:
                continue
            for index, row in df.iterrows():
                if row["element_type"] == val and row["name"] not in self.names and (self.main_teams.count(row["team"]) + self.teams.count(row["team"]))< 3:
                    self.price_constraint -= row["value"]
                    self.teams.append(row["team"])
                    self.names.append(row["name"])
                    self.subs.append(row.tolist())
                    break
        return self.subs


if __name__ == "__main__":

    #points = 0
    #for k in range(1,39):
    #    r = totw(k, True)
    #    print(r.find_totw())
    #    points += sum(r.extract_points())
    #print(points - 36*40)

    for k in range(1,39):
        r = totw(k, True, True)
        print(r.extract_subs())