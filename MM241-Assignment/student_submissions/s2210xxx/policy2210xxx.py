from policy import Policy
class Policy2210xxx(Policy):
    def __init__(self):
        self.save_area = 0
        self.save_cut = []
        self.idx = 0 

    def get_action(self, observation, info):
        # Lấy danh sách stocks và demands
        stocks = observation["stocks"]
        #demands = observation["products"]
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