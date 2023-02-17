from totw import totw
from toty import toty
import pandas as pd

class evaluate:

    def __init__(self, gws):

        self.gws = gws
        self.points_list = self.find_points_list()

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

    def total_points(self):

        points = 0
        points += self.find_triple_captain() # Increase points for the Triple Captain Chip
        self.gws[self.find_free_chip()[0]-1] = self.find_free_chip()[1]
        self.points_list = self.find_points_list()
        for gw in range(1,39):
            gw_points_list = self.points_list[gw-1] # Extract a specific gameweek
            print(gw_points_list)
            gw_points_list[gw_points_list.index(max(gw_points_list))] = gw_points_list[gw_points_list.index(max(gw_points_list))] * 2 # Multiply highest scoring player points by 2 for captaincy
            print(gw_points_list)
            points += sum(gw_points_list) # Add gameweek points to total points
        points -= self.find_deductable() # Deduct points for additional transfers made
        return points
    
    def find_deductable(self):

        sum = 0
        for val in range(0,37):
            sum += len(set(self.gws[val] + self.gws[val+1])) - 12
        if sum < 0:
            return 0
        else:
            return (4*sum)
    
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
        print("The Free Hit Chip will be played in Gameweek", free_hit_gameweek)
        free_hit = totw(free_hit_gameweek,True)
        return [free_hit_gameweek, free_hit.extract_indices()]
    
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
        print("The triple captaincy will be played in Gameweek", high_gameweek, "where the player", name, "scored", high_points, "points")
        return high_points


if __name__ == "__main__":

    a_list = [54, 78, 125, 33, 208, 83, 392, 394, 235, 403, 143]
    list1 = []
    for k in range(0,38):
        list1.append(a_list)
    s = evaluate(list1)
    print(s.total_points())

    list2 = []
    for k in range(1,39):
        r = totw(k,True)
        list2.append(r.extract_indices())
    t = evaluate(list2)
    print(t.total_points())