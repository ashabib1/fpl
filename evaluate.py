from totw import totw
from toty import toty
import pandas as pd

class evaluate:

    def __init__(self, gws, subs=[]):

        self.gws = gws
        self.points_list = self.find_points_list()
        self.subs = subs

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
    
    def find_points_list(self):
        
        full_points_list = []
        for gw in range(1,39):
            df = self.dataloader(gw) 
            points_list = [] # Create variable for current gameweek points list
            for val in self.gws[gw-1]:
                try:
                    df.loc[df['element']==val].values.tolist()[1][1]
                except:
                    x = 0
                else:
                    points_list.append(df.loc[df['element']==val].values.tolist()[0][1] + df.loc[df['element']==val].values.tolist()[1][1])
                    continue
                try: 
                    df.loc[df['element']==val].values.tolist()[0][1]
                except:
                    x = 0
                else:
                    points_list.append(df.loc[df['element']==val].values.tolist()[0][1])
            full_points_list.append(points_list) # Append gameweek points list to overall points list   
        return full_points_list

    # Find total number of points for a set of players
    def total_points(self):

        points = 0
        points += self.find_triple_captain() # Increase points for the Triple Captain Chip
        points -= self.find_deductable() # Deduct points for additional transfers made
        points += self.find_bench_boost()
        free_hit_chip = self.find_free_chip()# Applies the Free Hit Chip
        self.gws[free_hit_chip[0]-1] = free_hit_chip[1] # Change the gameweek players for the free hit chip
        self.points_list = self.find_points_list() # Reinitialise the points list - Due to Free Hit Chip played
        for gw in range(1,39):
            gw_points_list = self.points_list[gw-1] # Extract a specific gameweek
            gw_points_list[gw_points_list.index(max(gw_points_list))] = gw_points_list[gw_points_list.index(max(gw_points_list))] * 2 # Multiply highest scoring player points by 2 for captaincy
            points += sum(gw_points_list) # Add gameweek points to total points
        return points
    
    # Find number of deductable points
    def find_deductable(self):

        changes = []
        sum = 0
        for val in range(0,37):
            changes.append(len(set(self.gws[val] + self.gws[val+1])) - 12)
            sum += len(set(self.gws[val] + self.gws[val+1])) - 12
        first_wildcard = changes[0:18].index(max(changes[0:18])) # Find the maximum number of transfers in one gameweek for the first half of the season
        second_wildcard = changes[18:37].index(max(changes[18:37])) # Find the maximum number of transfers in one gameweek for the second half of the season
        print("The First Wilcard Chip will be played in Gameweek", first_wildcard + 2)
        print("The Second Wildcard Chip will be played in Gameweek", second_wildcard + 20)
        sum -= (max(changes[0:18]) + max(changes[18:37])) # Take away the transfer deductables for two gameweeks
        if sum < 0: # If less transfers were used than one per week, there should be no deductables
            return 0
        else: # If more transfers were used than one per week, there are four points deducted per transfer exceeded
            return (4*sum)
    
    # Find the gameweek for the Free Hit Chip
    def find_free_chip(self):

        totw_points = []
        for k in range(1,39):
            r = totw(k,True)
            totw_points.append(sum(r.extract_points()))
        weekly_points = []
        for k in range(0,38):
            weekly_points.append(sum(self.points_list[k]))
        totw_difference = [a - b for a, b in zip(totw_points, weekly_points)]
        free_hit_gameweek = totw_difference.index(max(totw_difference)) + 1
        print("The Free Hit Chip will be played in Gameweek", free_hit_gameweek, "earning an extra", max(totw_difference), "points")
        free_hit = totw(free_hit_gameweek,True)
        return [free_hit_gameweek, free_hit.extract_indices()]
    
    # find the gameweek for the Triple Captain Chip
    def find_triple_captain(self):
        high_gameweek = -1
        high_points = -1
        high_index = -1
        for gameweek in self.points_list:
            index = 0
            for player in gameweek:
                index += 1
                if player > high_points:
                    high_points = player
                    high_index = index
                    high_gameweek = self.points_list.index(gameweek) + 1
        final_index = self.gws[high_gameweek - 1][high_index - 1]
        df = self.dataloader(38)
        name = df.loc[df['element']==final_index].values.tolist()[0][0]
        print("The Triple Captain Chip will be played in Gameweek", high_gameweek, "where the player", name, "scored", high_points, "points")
        return high_points

    def find_bench_boost(self):
        
        if self.subs == []:
            return 0
        subs_points = []
        for k in range(1,39):
            df = self.dataloader(k)
            local_points = 0
            for val in self.subs[k-1]:
                try:
                    df.loc[df['element']==val].values.tolist()[0][1]
                except:
                    local_points += 0
                else:
                    local_points += df.loc[df['element']==val].values.tolist()[0][1]
            subs_points.append(local_points)
        print("The Bench Boost Chip will be played in Gameweek", subs_points.index(max(subs_points)) + 1, "earning an extra", max(subs_points), "points")
        return max(subs_points)

if __name__ == "__main__":

    a_list = [54, 191, 125, 33, 204, 392, 82, 394, 235, 403, 143]
    b_list = [524, 435, 434, 508]
    list1 = []
    list3 = []
    for k in range(0,38):
        list1.append(a_list)
        list3.append(b_list)
    s = evaluate(list1, list3)
    print(s.total_points())

    c_list = [356, 297, 33, 303, 12, 92, 212, 205, 208, 97, 272]
    d_list = [219, 301, 125, 558, 12, 398, 48, 208, 402, 403, 143]
    c_list_sub = [472, 435, 434, 508]
    d_list_sub = [147, 196, 319, 579]
    list_10, list_11 = [], []
    for k in list(range(0,19)):
        list_10.append(c_list)
        list_11.append(c_list_sub)
    for k in list(range(19,38)):
        list_10.append(d_list)
        list_11.append(d_list_sub)
    m = evaluate(list_10, list_11)
    print(m.total_points())

    list2 = []
    subs = []
    for k in range(1,39):
        r = totw(k,True)
        list2.append(r.extract_indices())
        subs.append(r.extract_subs())
    t = evaluate(list2, subs)
    print(t.total_points())

    list3 = []
    list4 = []
    for k in range(1,20):
        r = toty(2*k-1,2*k,True)
        r.find_toty()
        list3.append(r.find_elements())
        list3.append(r.find_elements())
        list4.append(r.extract_subs_elements())
        list4.append(r.extract_subs_elements())
    n = evaluate(list3, list4)
    print(n.total_points())