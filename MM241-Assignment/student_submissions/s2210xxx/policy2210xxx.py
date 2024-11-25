from policy import Policy

#Giai thuat nhanh-can
class BranchAndBound(Policy):
    def __init__(self):
        self.save_area = 0
        self.save_cut = []
        self.idx = 0 

    def get_action(self, observation, info):
        # Lấy danh sách stocks và demands
        stocks = observation["stocks"]
        #demands = observation["products"]git
        # Convert to list and copy items
        demands = observation["products"]
        # Sắp xếp demands theo diện tích giảm dần
        demands = sorted(demands, key=lambda x: x["size"][0] * x["size"][1], reverse=True)

        def branch_and_bound(stock_idx, current_area, remaining_demands, current_cut, idx , quantity ): 
            # idx chỉ là biến dùng giữ index của prod tiêp theo trongn truog hop stock ko lap duoc va phai xoa prod hien tai lap vao prod tiep theo
            if all(x <= 0 for x in quantity) : # kiểm tra xem đã lắp xong hết chưa  
                self.idx = 0 
                return {"stock_idx": stock_idx,"size": remaining_demands[idx]["size"], "position": remaining_demands[idx]["position"]}

            # Lấy thông tin stock
            stock = stocks[stock_idx]
            stock_w, stock_h = self._get_stock_size_(stock)

            # TODO Duyệt từng sản phẩm trong demands
            # TODO nếu có mảnh được thêm vào thì dừng giải thuật, để có thể chạy qua step render frame 
            for demand_idx, demand in enumerate(remaining_demands): # lấy ra id của sản phẩm và kiểu sản phẩm
                if quantity[demand_idx] <= 0:
                    continue
                prod_w, prod_h = demand["size"] # lấy ra chiều rộng và cao của sản phẩm
                if(stock_w  < prod_w  or stock_h < prod_h): continue
                # Thử đặt sản phẩm vào stock
                if(demand_idx < idx):
                    continue
                
                for x in range(stock_w - prod_w + 1):
                    for y in range(stock_h - prod_h + 1):
                        if(quantity[demand_idx] <= 0): break
                        if self._can_place_(stock, (x, y), (prod_w, prod_h)):
                            # Đặt sản phẩm
                            # Cập nhật thông tin
                            #self._place_piece(stock, (x, y), (prod_w, prod_h), demand_idx)
                            self.save_cut.append({"stock_idx": stock_idx, "size": demand["size"], "position": (x, y), "prod_id": demand_idx})
                            self.save_area = current_area + (prod_w * prod_h) # cập nhật diện tích đã cắt của stock hiện tại
                            # demand["quantity"] -= 1
                            quantity[demand_idx] -= 1
                            if all(x <= 0 for x in quantity):  
                                self.idx = 0 
                            return {"stock_idx": stock_idx, "size": demand["size"], "position": (x, y)}
                    if(quantity[demand_idx] <= 0): break
            # next_idx dùng để gọi đến product tiếp theo nếu như 3. la False 
            next_idx = self.save_cut[-1]["prod_id"] + 1
            if next_idx < len(remaining_demands): # kiểm tra xem next_idx k phải là prod cuối
                some_max = max(prod["quantity"] for prod in remaining_demands)
                least = min( prod["size"][0] * prod["size"][1] for prod in remaining_demands if prod["quantity"] > 0)
                area = current_area - current_cut[-1]["size"][0] * current_cut[-1]["size"][1]  +  some_max*least
                if(area > self.save_area ): 
                    # if kiểm tra đk để làm nhánh cận
                    # - current_cut[-1]["size"][0] * current_cut[-1]["size"][1]
                    pos = self.save_cut[-1]["position"]
                    size = self.save_cut[-1]["size"]

                    # xóa khỏi stock 
                    self._remove_piece(stock, pos, size)
                    remaining_demands[self.save_cut[-1]["prod_id"]]["quantity"] += 1
                    quantity[self.save_cut[-1]["prod_id"]] += 1 
                    self.save_cut.pop()
                    self.save_area = self.save_area - current_cut[-1]["size"][0] * current_cut[-1]["size"][1]

                    # nếu prod đặt đc và tồn tại prod
                    if(self._can_place_(stock, pos, remaining_demands[next_idx]["size"]) and remaining_demands[next_idx]["quantity"] > 0):
                        self._place_piece(stock,pos, remaining_demands[next_idx ]["size"], next_idx)
                        self.save_area = self.save_area + remaining_demands[next_idx ]["size"][0] * remaining_demands[next_idx ]["size"][1]
                        self.save_cut.append({"stock_idx": stock_idx, "size": remaining_demands[next_idx ]["size"], "position": pos, "prod_id": next_idx})
                        # remaining_demands[next_idx]["quantity"] -= 1
                        quantity[next_idx] -= 1
                        # return {"stock_idx": stock_idx, "size": remaining_demands[next_idx ]["size"], "position": pos}
                        retvalue = branch_and_bound(stock_idx, self.save_area, remaining_demands, self.save_cut, next_idx, quantity)
                        if all(x <= 0 for x in quantity):  
                            self.idx = 0 
                        return retvalue
                    else:
                        self._place_piece(stock, pos,size, next_idx - 1 )
                        self.save_cut.append({"stock_idx": stock_idx, "size": size, "position": pos, "prod_id": next_idx - 1})
                        self.save_area = current_area + size[0] * size[1] # cập nhật diện tích đã cắt của stock hiện tại
                        remaining_demands[next_idx - 1]["quantity"] -= 1
                        quantity[next_idx - 1] -= 1
                        self.idx += 1
                        if all(x <= 0 for x in quantity):  
                            self.idx = 0 
                        return {"stock_idx": stock_idx, "size": size, "position": pos}

                else:
                    self.idx += 1
            else :
                self.idx += 1
            if all(x <= 0 for x in quantity):  
                self.idx = 0 
            return {"stock_idx": -1, "size": (0, 0), "position": (-1, -1)}
        # Chạy giải thuật
        quantity = [demand["quantity"] for demand in demands]
        ret =  branch_and_bound(self.idx, self.save_area, demands, self.save_cut , -1, quantity)
        if all(x <= 0 for x in quantity ):  self.idx = 0 
        return ret

    # method đặt các product vào stock
    def _place_piece(self, stock, position, size, demand_idx):
        x, y = position
        w, h = size
        stock[x : x + w, y : y + h] = demand_idx
    # method xóa các product khỏi stock
    def _remove_piece(self, stock, position, size):
        x, y = position
        w, h = size
        stock[x : x + w, y : y + h] = -1

#Giai thuat luyen thep
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