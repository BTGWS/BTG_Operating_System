import Disk_Operation as DO
import math
from BTG_Operating_System import *
temp = None

# 创建文件
def Create_File(filepath:str, filename:str, fileclass:int, file_content:str = '') -> bool:
    '''
    1.判断磁盘容量是否已满
    2.判断当前目录容量是否已满      注：根目录容量只有64B
    3.创建文件控制块
    '''
    


    isEmpty = True
    isError = False

    filename_list = filename.split('.')
    
    
    if filepath[2] == '\\':
        filepath_list = filepath.split('\\')[0:-1]
    elif filepath[2] == '/' and filepath[3] != '/':
        filepath_list = filepath.split('/')[0:-1]
    elif filepath[2] == '/' and filepath[3] == '/':
        filepath_list = filepath.split('//')[0:-1]
    else:
        # 文件路径非法
        isError = True

    
    # 读取磁盘全部内容
    disk_data = DO.disk_open(filepath_list[0])
    # 获取FAT
    FAT = []
    for i in range(128):
        FAT.append(disk_data[i])

    # 判断磁盘容量是否已满
    if DO.disk_isfull(filepath_list[0]) == True:
        isEmpty = False
        print('磁盘已满')

    # 判断是否在根目录操作，并判断是否有空位和是否重名
    if len(filepath_list) == 1:
        # 判断目录是否已满
        if DO.get_create_position_num(filepath_list, disk_data) == True:
            isEmpty = False
            print('根目录已满')
        else:
            
            file_pointer = 0
            # return '根目录有空位'
            # 判断是否有重名文件
            FCB_list = get_path_allFCB_bytes(filepath_list[file_pointer], disk_data)
            
            if is_duplication(FCB_list, filename_list, fileclass) == True:
                print('文件重复！')
                return False
    else:
        # 设置8字节全为0的列表
        empty_list = bytes([0]*8)
        # 文件指针
        file_pointer = 0
        # 文件指针指向的文件FCB
        catalogue_FCB = {}
        # 文件指针指向的文件FCB列表
        catalogue_FCB_bytes_list = []

        while(file_pointer < len(filepath_list)):
            
            catalogue_FCB_bytes_list = get_path_allFCB_bytes(filepath_list[file_pointer], disk_data, catalogue_FCB, FAT)
            
            file_pointer = file_pointer + 1

            if file_pointer == len(filepath_list):
                break

            folder_name_bytes = filename_to_bytes(filepath_list[file_pointer], 0)

            for i in range(len(catalogue_FCB_bytes_list)):
                if catalogue_FCB_bytes_list[i][0:4] == folder_name_bytes[0:4]:
                    catalogue_FCB = DO.bytes_to_FCB(catalogue_FCB_bytes_list[i])
            
            
            
        
        length = len(catalogue_FCB_bytes_list)
        for i in range(length + 1):
            # 如果没有位置
            if i == length:
                isEmpty = False
                print('没有位置')
            # 如果有位置
            elif catalogue_FCB_bytes_list[i] == empty_list:
                isEmpty = True
                break
        # 判断是否有重名文件
        if is_duplication(catalogue_FCB_bytes_list, filename_list, fileclass) == True:
            print('文件重复！')
            return False
        

    
    # 判断文件是否合法
    if __isFile(filename):
        isError = False      
    else:
        isError = True
        #print('文件名非法')
    
    if len(filename_list) == 1 and fileclass != 0:
        isError = True
    
    

    # 如果存储空间足够且文件合法则创建FCB
    if isEmpty == True and isError == False:
        
        # 创建目录文件
        if fileclass == 0 :
            #打开创建目录文件的窗体:
            new_FCB = Create_FCB(filepath_list, filename_list, fileclass, disk_data, FAT)
            #print(new_FCB)
            
        else:
            #打开创建其他文件的窗体:
            #创建其他文件
            new_FCB = Create_FCB(filepath_list, filename_list, fileclass, disk_data, FAT, file_content)
            #print(new_FCB)
    else:
        #print(isEmpty,isError)
        print('无法创建文件')
        return False
    
    DO.disk_io(filepath_list, 'in', filename_list, FAT, new_FCB, file_content)
    

    return True


# 创建文件控制块
def Create_FCB(filepath_list:str, filename_list:list, fileclass:int, disk_data, FAT, file_content:str = ''):
    
    FCB_temp = {
        # 'File_path' : '',
        'File_name' : '',               # 3B
        'File_type' : '',               # 2B
        'Disk_startblock' : 0,          # 1B    0~255
        'File_size' : 0,                # 1B    0~255   最大存储相当4个磁盘块大小的文件
        'File_class' : 2                # 1B    0代表文件目录，1代表系统文件，2代表普通文件
    }
    
    if fileclass == 0:
        FCB_temp['File_name'] = filename_list[0]            # 转成规范文件名
        #FCB_temp['File_type'] = filename_list[-1]           # 获得文件后缀
        FCB_temp['Disk_startblock'] = DO.get_start_block(filepath_list, disk_data, FAT)                 # 获得起始盘块位置
        FCB_temp['File_size'] = get_File_len(file_content)                                              # 获取文件内容长度
        FCB_temp['File_class'] = fileclass
    else:
        #FCB_temp['File_path'] = filepath
        FCB_temp['File_name'] = filename_list[0]            # 转成规范文件名
        FCB_temp['File_type'] = filename_list[-1]           # 获得文件后缀
        FCB_temp['Disk_startblock'] = DO.get_start_block(filepath_list, disk_data, FAT)                 # 获得起始盘块位置
        FCB_temp['File_size'] = get_File_len(file_content)                                              # 获取文件内容长度
        FCB_temp['File_class'] = fileclass
    
    return FCB_temp
    

# 判断文件是否合法
def __isFile(exten:str):
    if exten[0] == '.' or exten == '' :                   # 以'.'字符开头或无文件名
        return False
    else :
        exten_list = exten.split('.')
        if len(exten_list[0]) > 3 :                       # 文件名过长
            return False
        elif len(exten_list) == 1 :                       # 只有文件名无后缀名
            return True
        elif exten_list[-1] in ('t', 'tx', 'e', 'ex') :   # 有后缀的合法后缀名
            return True
        else :
            return False


# 获取文件长度
def get_File_len(file_content:str):
    # 将文件内容转换为字节型
    # 在utf-8编码下汉字占三个字节
    content = file_content.encode('utf-8')
    return len(content)



# 读取文件
def read_File(file_path_name:str):
    
    if file_path_name[2] == '\\':
        file_list = file_path_name.split('\\')
    elif file_path_name[2] == '/' and file_path_name[3] != '/':
        file_list = file_path_name.split('/')
    elif file_path_name[2] == '/' and file_path_name[3] == '/':
        file_list = file_path_name.split('//')
    
    filepath_list = file_list[0:-1]
    filename_list = file_list[-1].split('.')
    
    


    return DO.disk_io(filepath_list, 'out',filename_list)
    
    


# 将文件名及后缀转换成字节型
def filename_to_bytes(filename_list:list, option_name:int = 1):
    file_name = ''
    file_type = ''
    
    # 如果是目录文件
    if option_name == 0:
        file_name = filename_list[0].encode()
    else:
        file_name = filename_list[0].encode()
        file_type = filename_list[-1]
    while len(file_name) < 3:
        file_name += ' '.encode()
    
    fb = file_name + '{0:2}'.format(file_type).encode()
    return fb


# 判断文件是否重名
def is_duplication(FCB_list:list, filename_list:list, file_class = 0):
    exist = False
    # 将文件名转换成字节型
    filename_bytes = filename_to_bytes(filename_list, file_class)

    for i in range(len(FCB_list)):
        # 目录下存在此文件
        if FCB_list[i][0:4] == filename_bytes[0:4]:
            exist = True
            break
    return exist


# 获取当前目录下的所有FCB
def get_path_allFCB_bytes(filepath_name:str, disk_data, FCB = {}, FAT = []):
    FCB_bytes_list = []
    # 当前路径在根目录
    if filepath_name in ('C:', 'c:', 'D:', 'd:'):
        root_data_list = []
        # 截取磁盘第三块物理盘块中内容
        root_data = disk_data[128:192]
        # 将根目录64B分成8块，每块8B截取到列表
        for i in range(8):
            root_data_list.append(root_data[i*8:i*8+8])
        FCB_bytes_list = root_data_list
    else:
         # 获取目标文件FCB中起始盘块号
        start_block_number = DO.get_FCB_block_num(FCB)
        
        # 获取文件存储区所在的所有块
        FAT_list = []
        FAT_list.append(start_block_number)
        for i in range(start_block_number, 128):
            if FAT[i] == 129:
                break
            else:
                FAT_list.append(FAT[i])
        
        # 读取文件目录下全部FCB
        for i in FAT_list:
            pointer = i*64
            for j in range(8):
                FCB_bytes_list.append(disk_data[pointer+j*8:pointer+j*8+8])
    return FCB_bytes_list


# 进入当前目录
def enter_folder(filepath_list:list, FAT, disk_data) -> int:
    position = -1
    next_pointer = 1                  # 文件路径中指向文件目录的指针
    folder_name_list = filepath_list
    temp_data_list = []
    temp_FCB = {}
    now_start_block_num = 0           # 当前指针所在位置的盘块号

    # 设置8字节全为0的列表
    empty_list = bytes([0]*8)

    # 获取根目录下所有字节型FCB
    
    data_list = get_path_allFCB_bytes(folder_name_list[next_pointer - 1], disk_data)
    

    # 如果在根目录
    if next_pointer == len(folder_name_list):
            # 获取此目录下所有字节型FCB
            temp_data_list = data_list
    else:
        # 将文件名转换成字节型
        filename_bytes = filename_to_bytes(folder_name_list[next_pointer], 0)
        for i in range(8):
            # 如果找到此文件
            if data_list[i][0:5] == filename_bytes:
                position = i
                break
        # 获取目标文件的字节型FCB并转换格式
        FCB_bytes = data_list[position]
        target_FCB = DO.bytes_to_FCB(FCB_bytes)
        temp_FCB = target_FCB
        # 获取目标文件FCB中起始盘块号
        start_position = DO.get_FCB_block_num(target_FCB)
        #获取当前起始盘块号
        now_start_block_num = start_position
        # 文件目录指针指向文件路径中下一个文件目录
        next_pointer = next_pointer + 1
    #-----------------------------------------------------
        while(next_pointer < len(folder_name_list)):
            data_list = []
            # 获取此目录下所有字节型FCB
            data_list = get_path_allFCB_bytes(folder_name_list[next_pointer], disk_data, temp_FCB, FAT)

            temp_data_list = data_list

            # 将文件目录名转成字节
            filename_bytes = filename_to_bytes(folder_name_list[next_pointer], 0)
            for i in range(len(data_list)):
                # 如果找到此文件
                if data_list[i][0:5] == filename_bytes:
                    position = i
                    break

            # 获取目标文件的字节型FCB并转换格式
            FCB_bytes = data_list[position]
            target_FCB = DO.bytes_to_FCB(FCB_bytes)
            temp_FCB = target_FCB
            # 获取目标文件FCB中起始盘块号
            start_position = DO.get_FCB_block_num(target_FCB)
            #获取当前起始盘块号
            now_start_block_num = start_position
            # 文件目录指针指向文件路径中下一个文件目录
            next_pointer = next_pointer + 1
    #-----------------------------------------------------
        # 获取此目录下所有字节型FCB
        data_list = get_path_allFCB_bytes(folder_name_list[next_pointer-1], disk_data, temp_FCB, FAT)

        temp_data_list = data_list

    while True:
        length = len(temp_data_list)
        # temp_data_list当前目录现有的盘块存储的内容
        for pointer in range(length + 1):
            # 当pointer指向第 length + 1 个盘块时，表示当前目录现有盘块已满，需申请新盘块，返回True
            if pointer == length + 1:
                return True
            # 当前目录存在空位置
            if temp_data_list[pointer] == empty_list:
                # 获得起始位置   
                return pointer*8 + now_start_block_num*64
                #return False

# 删除文件
def Delete_File(file_path_name:str):
    if file_path_name[2] == '\\':
        file_list = file_path_name.split('\\')
    elif file_path_name[2] == '/' and file_path_name[3] != '/':
        file_list = file_path_name.split('/')
    elif file_path_name[2] == '/' and file_path_name[3] == '/':
        file_list = file_path_name.split('//')
    
    filepath_list = file_list[0:-1]
    filename_list = file_list[-1].split('.')

    # 获得磁盘内容 
    disk_data = DO.disk_open(filepath_list[0])
    # 获取FAT
    FAT = []
    for i in range(128):
        FAT.append(disk_data[i])

    delete_FCB(filepath_list, filename_list, FAT, disk_data)



    return True


# 删除文件FCB
def delete_FCB(filepath_list, filename_list, FAT, disk_data):
    # 设置父盘块号
    parent_block = 2
    # 设置8字节全为0的列表
    empty_list = bytes([0]*8)
    # 文件指针
    file_pointer = 0
    # 文件指针指向的文件FCB
    file_FCB = {}
    # 文件指针指向的文件的字节型FCB
    file_FCB_bytes = []
    # 文件指针指向的文件的字节型FCB列表
    file_FCB_bytes_list = []
    # 修改磁盘FCB信息的起始指针
    start_pointer = -1


    # 遍历到需要删除的文件所在的目录下
    while(file_pointer < len(filepath_list)):
        if file_FCB != {}:
            parent_block = file_FCB['Disk_startblock']

        file_FCB_bytes_list = get_path_allFCB_bytes(filepath_list[file_pointer], disk_data, file_FCB, FAT)
            
        file_pointer = file_pointer + 1

        if file_pointer == len(filepath_list):
            break

        folder_name_bytes = filename_to_bytes(filepath_list[file_pointer], 0)

        for i in range(len(file_FCB_bytes_list)):
            if file_FCB_bytes_list[i][0:4] == folder_name_bytes[0:4]:
                file_FCB = DO.bytes_to_FCB(file_FCB_bytes_list[i])

    for i in range(len(file_FCB_bytes_list)):
        # 获取字节型文件FCB
        file_FCB_bytes = file_FCB_bytes_list[i]
        # 将字节型FCB转化成普通形式
        file_FCB = DO.bytes_to_FCB(file_FCB_bytes)

        # 找到要删除的文件，回收为此文件内容分配出去的盘块，并将此文件的FCB置空
        if len(filename_list) == 1:
            # 如果是目录文件
            filename_bytes = filename_to_bytes(filename_list, 0)
        else:
            # 如果是普通文件
            filename_bytes = filename_to_bytes(filename_list, 1)
        if file_FCB_bytes[0:5] == filename_bytes:
            # 获取需要修改的FCB在磁盘中起始位置
            start_pointer = i*8 + parent_block*64
            # 获取更新后的FAT
            FAT = DO.return_block(file_FCB['Disk_startblock'], disk_data, FAT)
            # 获取修改后的字节型文件FCB
            file_FCB_bytes = empty_list
            break

    with open('Disk_'+filepath_list[0][0], 'rb+') as disk:
        
        # 更新磁盘中FCB信息
        disk.seek(start_pointer)
        temp = file_FCB_bytes
        disk.write(temp)
        # 更新FAT
        DO.update_FAT(file_FCB['Disk_startblock'], FAT, disk)

    
    return True



# 修改文件
def Update_File(file_path_name:str, new_content:str) -> bool:
    if file_path_name[2] == '\\':
        file_list = file_path_name.split('\\')
    elif file_path_name[2] == '/' and file_path_name[3] != '/':
        file_list = file_path_name.split('/')
    elif file_path_name[2] == '/' and file_path_name[3] == '/':
        file_list = file_path_name.split('//')
    
    filepath_list = file_list[0:-1]
    filename_list = file_list[-1].split('.')

    # 获得磁盘内容 
    disk_data = DO.disk_open(filepath_list[0])
    # 获取FAT
    FAT = []
    for i in range(128):
        FAT.append(disk_data[i])
    # 设置父盘块号
    parent_block = 2
    # 文件指针
    file_pointer = 0
    # 文件指针指向的文件FCB
    file_FCB = {}
    # 文件指针指向的文件的字节型FCB
    file_FCB_bytes = []
    # 文件指针指向的文件的字节型FCB列表
    file_FCB_bytes_list = []
    # 修改磁盘FCB信息的起始指针
    FCB_start_pointer = -1



    # 遍历到需要删除的文件所在的目录下
    while(file_pointer < len(filepath_list)):
        if file_FCB != {}:
            parent_block = file_FCB['Disk_startblock']
        file_FCB_bytes_list = get_path_allFCB_bytes(filepath_list[file_pointer], disk_data, file_FCB, FAT)
            
        file_pointer = file_pointer + 1

        if file_pointer == len(filepath_list):
            break

        folder_name_bytes = filename_to_bytes(filepath_list[file_pointer], 0)

        for i in range(len(file_FCB_bytes_list)):
            if file_FCB_bytes_list[i][0:4] == folder_name_bytes[0:4]:
                file_FCB = DO.bytes_to_FCB(file_FCB_bytes_list[i])

    for i in range(len(file_FCB_bytes_list)):
        # 获取字节型文件FCB
        file_FCB_bytes = file_FCB_bytes_list[i]
        # 将字节型FCB转化成普通形式
        file_FCB = DO.bytes_to_FCB(file_FCB_bytes)

        # 找到要删除的文件，回收为此文件内容分配出去的盘块，并将此文件的FCB置空
        if len(filename_list) == 1:
            # 如果是目录文件
            filename_bytes = filename_to_bytes(filename_list, 0)
        else:
            # 如果是普通文件
            filename_bytes = filename_to_bytes(filename_list, 1)
        if file_FCB_bytes[0:5] == filename_bytes:
            # 获取需要修改的FCB在磁盘中起始位置
            FCB_start_pointer = i*8 + parent_block*64
            # 获取更新后的FAT
            FAT = DO.return_block(file_FCB['Disk_startblock'], disk_data, FAT)
            # 获取更新后新申请的默认初始盘号
            file_FCB['Disk_startblock'] = DO.get_start_block(filepath_list, disk_data, FAT)
            # 获取修改后的字节型文件FCB
            file_FCB['File_size'] = get_File_len(new_content)
            file_FCB_bytes = DO.FCB_to_bytes(file_FCB)
            break
    with open('Disk_'+filepath_list[0][0], 'rb+') as disk:
        # 如果长度大于初始分配的一个盘块大小则申请新盘块
        if file_FCB['File_size'] > 64:
            # 申请新盘块，减去原来默认分配的一个盘块
            blocknum = math.ceil(file_FCB['File_size']/64) - 1
            DO.apply_new_block(file_FCB['Disk_startblock'], disk_data, FAT, blocknum)
        # 更新磁盘中FCB信息
        disk.seek(FCB_start_pointer)
        temp = file_FCB_bytes
        disk.write(temp)
        # 更新FAT
        DO.update_FAT(file_FCB['Disk_startblock'], FAT, disk)

        start = file_FCB['Disk_startblock']*64
        disk.seek(start)
        temp = new_content.encode()
        disk.write(temp)
        

    return True



# 命令解释器
def Command_interpreter(command_list:list):
    
    cin = ''
    if command_list == []:
        return '请输入命令'
    command = command_list[0]

    if len(command_list) == 2:
        file_path_name = command_list[-1]
    elif len(command_list) == 3:
        file_path_name = command_list[-2]       
        cin = command_list[-1]
    if len(str(file_path_name).split('/')) == 1:
        return False
    name = str(file_path_name).split('/')[-1]
    
    if command in ('create', 'Create'):
        
        if len(name.split('.')) == 1:
            flag = Create_File(file_path_name, name, 0)
        else:
            flag = Create_File(file_path_name, name, 2, cin)
        return flag
    elif command in ('open', 'Open'):
        file_connect = read_File(file_path_name)
        global temp
        try:
            temp = Create_File_window()
            temp.open_file(file_path_name,file_connect)
            return True
        except BaseException:
            return False
        
    elif command in ('write', 'Write'):
        flag = Update_File(file_path_name, cin)
        return flag
    elif command in ('Reset', 'reset'):
        DO.init_disk(name)
        return True
    elif command in ('Delete', 'delete'):
        f = True
        file_path_list = []
        ret = DO.find_file(name, file_path_list)

        if file_path_list == []:
            f == False
        if f == True:
            flag = FO.Delete_File(file_path_name)
        return flag
    else:
        return False

