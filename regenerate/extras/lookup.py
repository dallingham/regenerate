
def lookup_from_address(project, address):

    dbfiles = [os.path.join(base, i) for i in project.get_register_paths()]

    (mapping, keys) = get_mappings(dbfiles, project)

    for filename in dbfiles:
        db = RegisterDb()
        db.read_xml(filename)
        for key in db.get_keys():
            reg = db.get_register(key)

            for i in [j for j in db.instances]:
                my_map = project.get_address_maps()
                for x in my_map:
                    if address == i[1] + reg.address + my_map[x]:
                        INST = x
                        BLK = db.module_name
                        display_register_page(reg, project, i[0], db, address)
                        return
    display_main()
    
