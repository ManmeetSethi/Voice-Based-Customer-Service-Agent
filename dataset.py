import pickle


def getDataFromPhone(phone):
    with open('name.pickle', 'rb') as handle:
        name_pkl = pickle.load(handle)

    with open('phone.pickle', 'rb') as handle:
        phone_pkl = pickle.load(handle)

    flag = 0
    for i in phone_pkl.keys():
        if str(phone_pkl[i])==phone:
            uid = i
            flag = 1

    order_id = ''
    if flag==1:
        name = name_pkl[uid]
        return name, uid
    else:
        return -1, -1

def getRecords(uid):
    with open('filename.pickle', 'rb') as handle:
        filename = pickle.load(handle)

    records = filename[uid]
    return records

def checkOrderId(order_id, uid):
    with open('filename.pickle', 'rb') as handle:
        filename = pickle.load(handle)

    records = filename[uid]
    record = -1
    for i in records:
        if i[0]==order_id:
            record = i
            break

    return record

# with open('phone.pickle', 'rb') as handle:
#     phone_pkl = pickle.load(handle)
#
# print(phone_pkl)
