import { PunchBridge } from './PunchBridge.js'
import { Selector } from './Selector.js'
const config = window.config

export default class DataSynchronizer {
    static punchBridge = null
    constructor() {
        this.mongoBridgeURL = config.mongoBridgeURL;
        DataSynchronizer.punchBridge = new PunchBridge({ host: config.pouchDBServer, port: config.pouchDBPort, database: config.pouchDBDatabase })
        this.initPunchBridge();
        //console.log("Initializing DataSynchronizer...")
    }

    async initPunchBridge() {
        if (config.syncRemoteCouchdb) {
            await DataSynchronizer.punchBridge.createDB({
                "fetch_url": `http://${config.pouchDBServer}:${config.pouchDBPort}/${config.pouchDBDatabase}`
                , "auth_username": config.pouchDBUsername
                , "auth_password": config.pouchDBPassword
                , "name": config.pouchDBDatabase
            })
        } else {
            await DataSynchronizer.punchBridge.createDB({
                "name": config.pouchDBDatabase
            })
        }

    }
    async getData(collection, queryOptions) {

        let recordData = await DataSynchronizer.punchBridge.find(queryOptions);
        recordData = Object.getOwnPropertyNames(recordData).map((x) => x.toLowerCase()).indexOf('docs') > -1 ? recordData['docs'] : recordData;
        //console.log(`recordData: ${JSON.stringify(recordData)}`)
        return { "name": collection, "data": recordData }

    }

      



    sync(collectionInfo) {
        
        let matchingFields =  collectionInfo.matchingFields
        let watchedFields  =  collectionInfo.watchedFields
        let query          = null
        let selector       = collectionInfo.selector?collectionInfo.selector:{}
        let mode           = collectionInfo.mode?collectionInfo.mode:'update'
        let collection     = collectionInfo.collectionName
        let idField        = collectionInfo.idField?collectionInfo.idField:null;

        //console.log(`Synchronizing ${collection}...`);
        try {

            if (mode == 'append'){
                let recordSelect  = new Selector([{ 
                    field: "table_name"
                    ,value: collection
                    ,operator:Selector.EQ
                  }]
                  
                  )  
                 //console.log(JSON.stringify(recordSelect))
                 return DataSynchronizer.punchBridge.find({selector: recordSelect}).then((meta)=>{
                     //console.log(`idField: ${idField}`)
                     let maxId    = -1
                     meta['docs'].forEach(element => {
                        maxId =  element[idField]> maxId?element[idField]:maxId
                     });

                     query = maxId
                     //console.log(`query: ${maxId}`)
                     let fetchUrl = query ? this.mongoBridgeURL + collection + '/' + query : this.mongoBridgeURL + collection;
                     return $.ajax({
                     url: fetchUrl
                     , type: 'GET'
                     , headers: {
                         'Access-Control-Allow-Origin': '*'
                         , 'Content-Type': 'application/json'
                         , 'Accept': 'application/json'
                     }
                     , dataType: 'json'
                     , success: function (results) {

                         results = results.map((result)=>{
                               return {...result,'table_name': collection}
                         })
                        
                        return DataSynchronizer.punchBridge.appendDocs(results, { 'selector': selector, 'limit': results.length, 'matchingFields': matchingFields, 'watchedFields': watchedFields })
                     }
                     , error: function (error) {
                         console.log(error)
                         return error
                     }
                 })

                  })

            } else if (mode=='update'){
                if (query && Object.getOwnPropertyNames(query).length > 0) {
                    query = JSON.stringify(query);
                }
                let fetchUrl = query ? this.mongoBridgeURL + collection + '/' + query : this.mongoBridgeURL + collection;
                return $.ajax({
                url: fetchUrl
                , type: 'get'
                , headers: {
                    'Access-Control-Allow-Origin': '*'
                    , 'Content-Type': 'application/json'
                    , 'Accept': 'application/json'
                }
                , dataType: 'json'
                , success: function (results) {

                    results = results.map((result)=>{
                          
                          return {...result,'table_name': collection}
                    })
                    let selectorOption = [{ 
                        field: "table_name"
                        ,value: collection
                        ,operator:Selector.EQ
                      }]
                    return DataSynchronizer.punchBridge.syncDocs(results, { 'selector': selectorOption, 'limit': results.length} , {'matchingFields': matchingFields, 'watchedFields': watchedFields })

                }
                , error: function (error) {
                    console.log(error)
                    return error
                }
            });
        }

        } catch (e) {
            console.log(e)
        }
    }


}


