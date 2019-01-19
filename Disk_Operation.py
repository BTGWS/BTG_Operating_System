import File_Operation as FO
import math

# 初始化磁盘(总大小为8K)
def init_disk(filepath_list:list): 

    with open('Disk_'+filepath_list[0][0], 'wb+') as c:
        #磁盘C有128个盘块
        for i in range(128):
            #每个盘块大小为64字节(64Byte)
            c.write(bytes([0]*64))


    # 磁盘前三块不分配给用户
    # 前两块保存FAT，FAT大小为128B，表示128个物理块
    # 第三块保存根目录，大小为64B，根目录下最多保存8个FCB，FCB大小为8B
    # 因为磁盘前三块不分配给用户，所以对FAT前三个字节初始化
    with open('Disk_'+filepath_list[0][0], 'rb+') as c:
        #从文件开头开始
        c.seek(0)
        for i in range(3):
            c.write(bytes([129]))


# 获取磁盘存储首盘块
def get_FCB_block_num(FCB:dict):
    index = FCB['Disk_startblock']
    return index

# 申请存储文件内容的起始磁盘块号
def get_start_block(filepath_list:list, disk_data, FAT):
    # 盘块号
    position = -1   
    
    # 申请盘块号
    for i in range(128):
        if FAT[i] == 0:
            position = i
            FAT[position] = 129
            break

    return position

# 申请新的存储盘块
def apply_new_block(pre_position:int, disk_data, FAT, blocknum:int):
    position = -1
    # 128个物理块
    for i in range(128):
        if FAT[i] == 0:
            position = i
            FAT[position] = 129
            # 需申请的磁盘块数目减一
            blocknum = blocknum - 1
            # 将FAT中上一个盘块内容指向当前块
            FAT[pre_position] = position
            if blocknum != 0:
                pre_position = position
                continue
            else:
                break

    return True

# 归还分配的存储盘块
def return_block(pre_position:int, disk_data, FAT):
    # 当前盘块指针指向当前文件内容分配到的起始盘块号
    now_position = pre_position
    # 当盘块指针不为129时继续向下一个盘块号推进
    while(now_position != 129):
        # 获取下一个盘块号
        next_position = FAT[now_position]
        # 当此盘块分配出去时
        if FAT[now_position] != 0:
            # 收回此盘块
            FAT[now_position] = 0
            # 推进当前盘块指针
            now_position = next_position

    return FAT



# 更新FAT
def update_FAT(pointer:int, FAT:list, disk):

    disk.seek(pointer)
    # 将更新后的FAT写入磁盘
    for i in range(pointer, 128):
        disk.write(bytes([FAT[i]]))


# 获取创建的新文件FCB需要在的位置
def get_create_position_num(filepath_list:list, disk_data, FAT = []):

    # 新文件起始指针
    start_pointer = -1
    # 设置8字节全为0的列表
    empty_list = bytes([0]*8)
    
    # 在根目录下创建文件时
    if len(filepath_list) == 1:

        root_data_list = []
        # 截取磁盘第三块物理盘块中内容
        root_data = disk_data[128:192]
        # 将根目录64B分成8块，每块8B截取到列表
        for i in range(8):
            root_data_list.append(root_data[i*8:i*8+8])

            
        # 在根目录中
        while True:
            # 根目录所在的第三个盘块上最多储存8个FCB
            for pointer in range(9):
                # 当pointer指向第9个FCB时，已超出盘块下标范围，表示根目录已满，返回True
                if pointer == 8:
                    return True
                # 根目录存在空位置
                if root_data_list[pointer] == empty_list:
                    # 获得起始位置   
                    return pointer*8+128
                    #return False
                
                
    else:
        start_pointer = FO.enter_folder(filepath_list, FAT, disk_data)

    return start_pointer
    
        

# 磁盘输入输出
def disk_io(filepath_list:list, IOname:str, filename_list = [], FAT:list = [], FCB = {}, content = ''):
    
    disk_data = disk_open(filepath_list[0])
    if FAT == []:
        # 获取FAT
        FAT = []
        for i in range(128):
            FAT.append(disk_data[i])
    

    with open('Disk_'+filepath_list[0][0], 'rb+') as d:
        if IOname == 'in':
            # 如果长度大于初始分配的一个盘块大小则申请新盘块
            if FCB['File_size'] > 64:
                # 申请新盘块，减去原来默认分配的一个盘块
                blocknum = math.ceil(FCB['File_size']/64) - 1
                apply_new_block(FCB['Disk_startblock'], disk_data, FAT, blocknum)
            # 写入FCB
            position = get_create_position_num(filepath_list, disk_data, FAT)
            d.seek(position)
            temp = FCB_to_bytes(FCB)
            d.write(temp)
            # 更新FAT
            update_FAT(FCB['Disk_startblock'], FAT, d)

            # 如果是txt、exe文件则写入文件内容
            if FCB['File_class'] in (1, 2):
        
                start = FCB['Disk_startblock']*64
                d.seek(start)
                temp = content.encode()
                d.write(temp)

            
        elif IOname == 'out':
            
            file_content = read_disk(filepath_list, filename_list, disk_data, FAT)
            return file_content
            # 打印内容
            #print(file_content)
    


# 读磁盘
def read_disk(filepath_list:list, filename_list:list, disk_data, FAT:list):
    
    position = -1
    next_pointer = 1                 # 文件路径中指向文件目录的指针
    folder_name_list = filepath_list
    temp_data_list = []
    temp_FCB = {}
    
    # 获取根目录下所有字节型FCB
    data_list = FO.get_path_allFCB_bytes(folder_name_list[next_pointer - 1], disk_data)
    # 如果在根目录
    
    if next_pointer == len(folder_name_list):
            # 获取此目录下所有字节型FCB
            temp_data_list = data_list
    else:
        # 将文件名转换成字节型
        filename_bytes = FO.filename_to_bytes(folder_name_list[next_pointer], 0)
        for i in range(8):
            # 如果找到此文件
            if data_list[i][0:5] == filename_bytes:
                position = i
                break
        # 获取目标文件的字节型FCB并转换格式
        FCB_bytes = data_list[position]
        target_FCB = bytes_to_FCB(FCB_bytes)
        temp_FCB = target_FCB
        # 获取目标文件FCB中起始盘块号
        start_position = get_FCB_block_num(target_FCB)
        #获取当前起始盘块号
        now_start_block_num = start_position
        # 文件目录指针指向文件路径中下一个文件目录
        next_pointer = next_pointer + 1

        while(next_pointer < len(folder_name_list)):
            data_list = []
            # 获取此目录下所有字节型FCB
            data_list = FO.get_path_allFCB_bytes(folder_name_list[next_pointer], disk_data, temp_FCB, FAT)

            temp_data_list = data_list

            # 将文件目录名转成字节
            filename_bytes = FO.filename_to_bytes(folder_name_list[next_pointer], 0)
            for i in range(len(data_list)):
            # 如果找到此文件
                if data_list[i][0:5] == filename_bytes:
                    position = i
                    break

            # 获取目标文件的字节型FCB并转换格式
            FCB_bytes = data_list[position]
            target_FCB = bytes_to_FCB(FCB_bytes)
            temp_FCB = target_FCB
            # 获取目标文件FCB中起始盘块号
            start_position = get_FCB_block_num(target_FCB)
            #获取当前起始盘块号
            now_start_block_num = start_position
            # 文件目录指针指向文件路径中下一个文件目录
            next_pointer = next_pointer + 1

        # 获取此目录下所有字节型FCB
        data_list = FO.get_path_allFCB_bytes(folder_name_list[next_pointer-1], disk_data, temp_FCB, FAT)

        temp_data_list = data_list
    
    #==============================
    
    data_list = temp_data_list
    
    '''
    data_list = []
    # 获取此目录下所有字节型FCB
    data_list = FO.get_path_allFCB_bytes(filepath_list, disk_data)
    '''
    # 将文件名转换成字节型
    
    filename_bytes = FO.filename_to_bytes(filename_list)
    
    for i in range(len(data_list)):
        # 如果找到此文件
        if data_list[i][0:5] == filename_bytes:
            position = i
            
            break
    
    # 获取目标文件的FCB
    FCB_bytes = data_list[position]
    #print(position)
    target_FCB = bytes_to_FCB(FCB_bytes)
    #print(target_FCB)
    # 获取目标文件FCB中起始盘块号
    start_position = get_FCB_block_num(target_FCB)
    # 获取文件长度
    target_size = target_FCB['File_size']

    # 获取文件存储所在的所有块
    FAT_list = []
    FAT_list.append(start_position)
    for i in range(start_position, 128):
        if FAT[i] == 129:
            break
        else:
            FAT_list.append(FAT[i])
    
 
    connect = read_file_connect(start_position, target_size, FAT, disk_data)
    return connect

# 读取文件内容
def read_file_connect(start_position:int, target_size:int, FAT:list = [], disk_data = bytes(0)):
    # 获取文件存储所在的所有块
    if FAT == []:
        disk_data = disk_open('C:')
        # 获取FAT

        for i in range(128):
            FAT.append(disk_data[i])
    FAT_list = []
    FAT_list.append(start_position)
    for i in range(start_position, 128):
        if FAT[i] == 129:
            break
        else:
            FAT_list.append(FAT[i])
    

    # 读取文件
    content_bytes_list = []
    content_bytes = ''.encode()
    
    for i in FAT_list:
        pointer = i*64
        # 如果文件内容大小 小于等于 一个物理块的大小
        if target_size <= 64:
            content_bytes_list.append(disk_data[pointer:pointer+target_size])
        # 如果文件内容大小 大于 一个物理块的大小
        else:
            content_bytes_list.append(disk_data[pointer:pointer+64])
            target_size = target_size - 64
            continue

    for i in content_bytes_list:
        content_bytes += i
    # 输出
    
    con = content_bytes.decode()
    return con


# 查找文件，得到该文件FCB
def search_file_FCB(path:str, start_block:int = -1) -> list:
    search_path = 'C:'
    temp_path = ''
    position = -1
    target_FCB = {}
    dir_list = []
    # 设置8字节全为0的列表
    empty_list = bytes([0]*8)

    new_path = path.split('/')[0:-1][-1]
    print(new_path)
    if start_block != -1:
        target_FCB = {
            'File_name' : '',               # 3B
            'File_type' : '',               # 2B
            'Disk_startblock' : start_block,          # 1B    0~255
            'File_size' : 0,                # 1B    0~255   最大存储相当4个磁盘块大小的文件
            'File_class' : 0
        }
    
    disk_data = disk_open(search_path)

    # 获取FAT
    FAT = []
    for i in range(128):
        FAT.append(disk_data[i])

    file_FCB_bytes_list = FO.get_path_allFCB_bytes(new_path, disk_data, target_FCB, FAT)

    for i in range(len(file_FCB_bytes_list)):
            position = i
            # 获取目标文件的字节型FCB并转换格式
            target_FCB_bytes = file_FCB_bytes_list[position]
            target_FCB = bytes_to_FCB(target_FCB_bytes)
            
            dir_list.append(target_FCB)
    return dir_list

    

# 判断磁盘是否已满
def disk_isfull(diskpath:str):
    if diskpath in ('C:', 'c:'):
        diskname = 'Disk_C'
    elif diskpath in ('D:', 'd:'):
        diskname = 'Disk_D'
    with open(diskname, 'rb') as disk:
        for i in range(128):
            if disk.read(1) == bytes([0]):
                return False                   # 磁盘有剩余
        return True                            # 磁盘无剩余

# 打开磁盘并读取全部内容
def disk_open(diskpath:str):
    
    with open('Disk_'+diskpath[0], 'rb+') as disk:
        disk_data = disk.read()
    return disk_data
    

# 将FCB转换成字节
def FCB_to_bytes(temp:dict):
    # 将字符串型的文件名规范成字节型
    name = temp['File_name'].encode()
    while len(name) < 3:
        name += ' '.encode()
    # 将FCB中的信息转换成字节型
    FCB_bytes = name + '{0:2}'.format(temp['File_type']).encode() + bytes([temp['Disk_startblock'], temp['File_size'], temp['File_class']] )
    return FCB_bytes

# 将字节型FCB转换成普通格式FCB
def bytes_to_FCB(temp:bytes):
    #print(temp)
    temp_name = temp[:3].decode()
    FCB_temp = {
        # 'File_path' : '',
        'File_name' : temp_name,                # 3B
        'File_type' : temp[3:5].decode(),               # 2B
        'Disk_startblock' : temp[5:6][0],          # 1B    0~255
        'File_size' : temp[6:7][0],                # 1B    0~255   最大存储相当4个磁盘块大小的文件
        'File_class' : temp[7:8][0],               # 1B    0代表文件目录，1代表系统文件，2代表普通文件
    }


    return FCB_temp

# 查找找文件，返回绝对路径
def find_file(filename:str, file_path_list:list, FCB = {}, disk_data = [], FAT = [], now_path = ''):
    search_path = 'C:'
    temp_path = ''
    position = -1
    target_FCB = {}
    ret = ''
    # 设置8字节全为0的列表
    empty_list = bytes([0]*8)
    filename_list = filename.split('.')

    if now_path == '':
        now_path = search_path
    else:
        temp_path = now_path
    if FCB != {}:
        target_FCB = FCB
    if disk_data == []:
        disk_data = disk_open(search_path)

        # 获取FAT
        FAT = []
        for i in range(128):
            FAT.append(disk_data[i])

    file_FCB_bytes_list = FO.get_path_allFCB_bytes(now_path, disk_data, target_FCB, FAT)
    # 将文件名转换成字节型
    if len(filename_list) == 1:
        filename_bytes = FO.filename_to_bytes(filename_list, 0)
    else:
        filename_bytes = FO.filename_to_bytes(filename_list)

    for i in range(len(file_FCB_bytes_list)):
        # 如果找到此文件
        if file_FCB_bytes_list[i][0:5] == filename_bytes:
            position = i
            ret = temp_path + '/' + filename
            file_path_list.append(ret)
           


    for i in range(len(file_FCB_bytes_list)):
        # 如果找到一个文件目录
        if file_FCB_bytes_list[i] != empty_list and bytes_to_FCB(file_FCB_bytes_list[i])['File_class'] == 0:
            position = i
            # 获取目标文件的字节型FCB并转换格式
            target_FCB_bytes = file_FCB_bytes_list[position]
            target_FCB = bytes_to_FCB(target_FCB_bytes)
            temp_path = temp_path + '/' + str(target_FCB['File_name']).split()[0]
            ret = find_file(filename, file_path_list, target_FCB, disk_data, FAT, temp_path)
            if ret != False:
                break

    return ret
    

