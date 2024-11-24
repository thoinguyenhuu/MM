import random
import numpy as np
from policy import Policy

class SimulatedAnnealingPolicy(Policy):
    def __init__(self, initial_temperature=1000, cooling_rate=0.95, iterations=1000):
        # Khoi tao cac tham so cua giai thuat Simulated Annealing
        self.initial_temperature = initial_temperature # Nhiet do ban dau
        self.cooling_rate = cooling_rate # He so lam nguoi
        self.iterations = iterations # So lan lap

    def get_action(self, observation, info):
        # Lay thong tin tu observation
        stocks = observation["stocks"] # Danh sach khoi
        demands = observation["products"] # Danh sach san pham can cat

        # Chuyen doi demands thanh danh sach cac tu dien co them truong quantity
        demands_with_quantity = [{**d, "quantity": d["quantity"]} for d in demands]

        # Khoi tao giai phap ban dau
        best_solution = self.generate_initial_solution(stocks, demands_with_quantity)
        best_cost = self.calculate_cost(best_solution, demands_with_quantity)
        current_solution = best_solution
        current_cost = best_cost

        # Nhiet do hien tai
        temperature = self.initial_temperature

        # Lap qua cac lan lap
        for _ in range(self.iterations):
            # Tao giai phap lang gieng
            neighbor_solution = self.generate_neighbor(current_solution, stocks, demands_with_quantity)
            neighbor_cost = self.calculate_cost(neighbor_solution, demands_with_quantity)

            # Tinh su khac biet ve chi phi
            delta_cost = neighbor_cost - current_cost

            # Dieu kien chap nhan giai phap lang gieng
            if delta_cost < 0 or random.random() < np.exp(-delta_cost / temperature):
                current_solution = neighbor_solution
                current_cost = neighbor_cost

                # Cap nhat giai phap tot nhat
                if current_cost < best_cost:
                    best_solution = current_solution
                    best_cost = current_cost

            # Giam nhiet do
            temperature *= self.cooling_rate

        # Tra ve ket qua (vi tri dat san pham dau tien trong giai phap tot nhat)
        if best_solution:
            return best_solution[0]  
        else:
            return {"stock_idx": -1, "size": (0, 0), "position": (-1, -1)}

    def generate_initial_solution(self, stocks, demands):
        # Tao mot giai phap ban dau bang cach dat cac san pham mot cach ngau nhien
        solution = []
        stocks_copy = [np.copy(stock) for stock in stocks] # Tao ban sao de tranh sua doi stocks goc

        for demand in demands:
            placed = False
            for i, stock in enumerate(stocks_copy):
                w, h = demand["size"]
                for x in range(stock.shape[0] - w +1):
                    for y in range(stock.shape[1] - h + 1):
                        # Kiem tra xem co cho trong de dat san pham khong
                        if np.all(stock[x:x+w, y:y+h] == -1):  
                            stock[x:x+w, y:y+h] = demand["quantity"]
                            solution.append({"stock_idx": i, "size": demand["size"], "position": (x, y)})
                            placed = True
                            break
                    if placed:
                        break
                if placed:
                    break
        return solution


    def generate_neighbor(self, solution, stocks, demands):
        # Tao mot giai phap lang gieng bang cach thay doi vi tri cua mot san pham ngau nhien
        if not solution:
            return []
        
        new_solution = solution[:] # Tao ban sao
        index_to_change = random.randint(0, len(solution) - 1)
        original_placement = new_solution[index_to_change]

        # Tim vi tri moi ngau nhien cho san pham
        stock_index = original_placement["stock_idx"]
        stock = stocks[stock_index]
        w, h = original_placement["size"]
        
        new_x, new_y = -1,-1
        for x in range(stock.shape[0] - w + 1):
            for y in range(stock.shape[1] - h + 1):
                if np.all(stock[x:x + w, y:y + h] == -1):
                    new_x, new_y = x,y
                    break
            if new_x != -1:
                break
        
        if new_x != -1:
            original_x, original_y = original_placement["position"]
            stock[original_x:original_x + w, original_y:original_y + h] = -1 # Xoa khoi vi tri cu
            stock[new_x:new_x + w, new_y:new_y + h] = original_placement["quantity"]
            new_solution[index_to_change]["position"] = (new_x, new_y)

        return new_solution


    def calculate_cost(self, solution, demands):
        # Ham tinh chi phi: toi thieu so san pham chua duoc dat
        unplaced_items = sum(d["quantity"] for d in demands)
        for placement in solution:
            unplaced_items -= placement["quantity"]
        return unplaced_items