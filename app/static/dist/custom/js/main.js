import { RequestHandler, Preloader, Navbar, Sidebar ,ContentHeader, Footer,DisplayManager,DataSynchronizer,PunchBridge, Selector,DashboardTable } from './lib.js';


const syncInterval = window.config.syncInterval
const syncMode     = window.config.syncMode
const dataSynchronizer = new DataSynchronizer();
new DisplayManager()
window.DisplayManager = DisplayManager; // Workaround for RequestHandler importing DisplayManager
window.dataSynchronizer = dataSynchronizer; // Workaround for RequestHandler importing DataSynchronizer
const defaultVersionMap = {}
window.syncID = -1
window.requestHandler = new RequestHandler();
const config  = window.config
//window.isUpdateRunning= false
let  dashWorker = null;
let syncWorker  = null;
if (window.Worker) {
    dashWorker = new Worker("/static/dist/custom/js/dashboardWorker.js");
    syncWorker = new Worker("/static/dist/custom/js/worker.js");
}

$.fn.getPouchConnection = ()=>{  
  if (!window.punchBridge){

    window.punchBridge  =  new PunchBridge({ host: config.pouchDBServer, port: config.pouchDBPort, database: config.pouchDBDatabase })

  }
  return window.punchBridge 
}

if (Object.keys(DisplayManager.collectionVersionMap).length > 0) {
  window.config.syncInfo.forEach((collection) => { defaultVersionMap[collection.collectionName] = 0 })
  DisplayManager.collectionVersionMap = defaultVersionMap;
}

$.fn.showText = (id, test) => {

  alert(test + ' ' + id)
}

function isOnline() {
  return window.navigator.onLine;
}

function startSync() {

  let fetchRequests = [];
  if (window.syncID === -1) {

    window.syncID = setInterval(() => {

      if (isOnline()) {
        
        window.config.syncInfo.forEach((collection) => {
          dataSynchronizer.sync(collection).then((updateCount) => {

            if (updateCount > 0) {

              DisplayManager.collectionVersionMap[collection.collectionName] += 1
              fetchRequests.push(dataSynchronizer.getData(collection.collectionName, { 'selector': collection.selector}))
            }
          })

        });

        Promise.all(fetchRequests).then(results => {
          if (results && results.collection && results.data) {
            DisplayManager.updateCollection(results.collection, results.data)
          }
        })



      }

    }, syncInterval)


  } else if (window.syncID !== -1) {

    //console.log("Data sync is already running");

  }


}

function stopSync() {

  clearInterval(window.syncID);
  window.syncID = -1;
}


$.fn.isAlphaNumSpecial = (fieldValue)=>{
  let pattern      =  /^[ A-Za-z0-9_@./#&+-]*$/i
  let matchDetails =  fieldValue.match(pattern)
  if (matchDetails && matchDetails.length> 0){
   return true
  }else {
   return false
  }

}


$.fn.isFieldValidOld = (element)=>{
  let value =  $(element).val();
  if(value==="" || !$.fn.isAlphaNumSpecial(value)){
    $(element).addClass('is-invalid')
      $('#report-upload-bttn').attr('disabled','disabled')
  }else{
    $(element).removeClass('is-invalid')

      if(!$('#report-name-id').hasClass('is-invalid')  &&  !$('#report-type-id').hasClass('is-invalid')  && !$('#report-org-id').hasClass('is-invalid')){ 
        $('#report-upload-bttn').removeAttr('disabled')
        }
  }

}

$.fn.isFieldValid = (element,buttonID,siblingIDs)=>{
  let value =  $(element).val();
  if(value==="" || !$.fn.isAlphaNumSpecial(value)){
    $(element).addClass('is-invalid')
      $('#'+buttonID).attr('disabled','disabled')
  }else{
    $(element).removeClass('is-invalid');
     let  validCount = siblingIDs.length;
     for (let id of siblingIDs){
        //console.log(id)
        //console.log($('#'+id).hasClass('is-invalid'))
         if($('#'+id).hasClass('is-invalid') ){
            --validCount;
         }

     }
      if(validCount == siblingIDs.length){ 
        $('#'+buttonID).removeAttr('disabled')
      }
  }

}

$.fn.checkReportFile = (element)=>{
  let value = $(element).val()
 // console.log(`Report uploaded: ${value}`)
  if(value.length>0 && value.indexOf('.')>-1 &&  window.config.UPLOAD_EXTENSIONS.indexOf(value.split('.').pop().toString().toLowerCase()) > -1){ 
    $("#report-header").removeClass("card-warning")
    $("#report-header").addClass("card-primary")
    $("#report-title").html("DMARC Report Upload")
  }else{

    $("#report-header").removeClass("card-primary")
    $("#report-header").addClass("card-warning")
    $("#report-title").html("DMARC Report Upload - Please select a valid DMARC Report")

  }

}
$.fn.resetModal = ()=>{

$('#modal-content').html(`            <div class="modal-header">
<div id="dialog-header-span" class="modal-title col-12">
    <h5></h5>
</div>
<button type="button" class="close" data-dismiss="modal" aria-label="close">
    <span aria-hidden="true"> &times;</span>
</button>
</div>

<div class="modal-body" id="dialog-message-div">
<p>

</p>
</div>
<div class="modal-footer" id="dialog-footer-div">
<a href="#" type="button" class="btn btn-info" data-dismiss="modal" id="dialog-close-bttn">Close</a>
<div class="row" id="dialog-bttns" style="display:none"> </div>
</div>`)

}

$.fn.cancelDialog = ()=>{ 
  event.preventDefault();
  $.fn.closeDialog();
  $.fn.resetModal();
}

$.fn.uploadReport = () => {
    let modalOptions = {
      keyboard: false,
      focus: true,
      backdrop: 'static'
    }

  $('#modal-content').html(`
  <div class="card card-primary" id="report-header">
    <div class= "card-header">
    <h3 class="card-title" id="report-title" >DMARC Report Upload</h3>
              </div >
  <form id="report-upload-form">
    <div class="card-body">
      <div class="form-group">
        <label for="report-name-id">Report Name</label>
        <input type="text" name="report_name" class="form-control" id="report-name-id" placeholder="Enter Report Name">
      </div>
      <div class="form-group">
        <label for="report-type-id">Report Type</label>
        <input type="report_type" class="form-control" id="report-type-id" value="RUA" placeholder="Enter Report Type" disabled>
      </div>
      <div class="form-group">
        <label for="report-org-id">Report Organisation</label>
        <input type="report_org" class="form-control" id="report-org-id" placeholder="Report Organisation">
      </div>
      <div class="form-group"
        <label for="report-file-id">File input</label>
        <div class="input-group">
          <div class="custom-file">
            <input type="file" class="custom-file-input" id="report-file-id">
              <label class="custom-file-label" for="report-file-id">Choose file</label>
          </div>
        </div>
      </div>
    </div>
    <div class="card-footer">
      <div class="row">
          <div class="col-6" align="left">
              <button  id="upload-cancel-bttn" onclick="$.fn.cancelDialog()"  class="btn btn-secondary">Cancel</button>
          </div>
          <div class="col-6" align="right">
              <button id="report-upload-bttn" class="btn btn-primary">Upload</button>
          </div>
      </div>
    </div>
  </form>
  </div>`);
  $('#myModal').modal(modalOptions);
  $('#myModal').show();


  $('#report-name-id').on('change', (e)=>{ $.fn.isFieldValid(e.target, 'report-upload-bttn', ['report-name-id','report-type-id','report-org-id']) })
  $('#report-type-id').on('change', (e)=>{ $.fn.isFieldValid(e.target, 'report-upload-bttn', ['report-name-id','report-type-id','report-org-id']) })
  $('#report-org-id').on('change', (e)=>{ $.fn.isFieldValid(e.target, 'report-upload-bttn', ['report-name-id','report-type-id','report-org-id']) })


  $('#report-file-id').on('change', (e)=>{$.fn.checkReportFile(e.target)})

  $('#report-upload-bttn').on('click',(e)=>{
   
   let reportNameText      =  $('#report-name-id').val();
   let reportTypeText      =  $('#report-type-id').val();
   let reportOrgText       =  $('#report-org-id').val();
   let reportFile          =  $('#report-file-id').val();

   if ( reportNameText.length>0  && reportTypeText.length >  0 && reportOrgText.length > 0 && reportFile.length> 0){
  
   // $('#report-upload-form').attr('method','post');
    // $('#report-upload-form').attr('action','/api/report/upload');
     // $('#report-upload-form').attr('enctype','multipart/form-data')
      //$('#report-upload-form').submit() //convert to Ajax
      e.preventDefault();
      const formData = new FormData();
     // console.log($('#report-file-id').prop('files')[0])

      formData.append("report_name", reportNameText);
      formData.append("report_type", reportTypeText); 
      formData.append("report_org", reportOrgText); 
      formData.append("report_file",$('#report-file-id').prop('files')[0],reportFile);

      // const request = new XMLHttpRequest();
      // request.open("POST", "/api/report/upload");
      // request.send(formData);
      
      $.ajax({
        url: "/api/report/upload",
        type: "POST",
        data: formData,
        processData: false,
        contentType: false,
        //async: true,
        crossDomain: true,
        success:  (result)=> {
            new Promise( (resolve)=>{
             resolve( $.fn.resetModal())
            }).then(()=>{
              
              $.fn.showAlert('DMARC Report Uploaded Successful','success') 
            })
            //alert('DMARC Report Uploaded Successful')
           // 
        },
        error: (e)=>{

          new Promise( (resolve)=>{
            resolve( $.fn.resetModal())
           }).then(()=>{
            
             $.fn.showAlert('DMARC Report Uploaded Failed','danger') 
           })

        }
    });

   }else { 
      

      $.fn.isFieldValid('#report-name-id', 'report-upload-bttn', ['report-name-id','report-type-id','report-org-id']) 
      $.fn.isFieldValid('#report-type-id', 'report-upload-bttn', ['report-name-id','report-type-id','report-org-id']) 
      $.fn.isFieldValid('#report-org-id', 'report-upload-bttn', ['report-name-id','report-type-id','report-org-id']) 
          
       if(reportFile.length == 0){
          //console.log("Report file is empty")
          $("#report-header").removeClass("card-primary")
          $("#report-header").addClass("card-warning")
          $("#report-title").html("DMARC Report Upload - Please select a valid DMARC Report")
       }
       e.preventDefault();
     
   }

  })

}


$.fn.drawLineChart=(data)=>{
  let  dateLabels = []
  let passData = []
  let failData = []
   for(let row of data){
      dateLabels.push(row.report_metadata_begin_date.split(' ')[0])
          let passCount = 0;
          let failCount = 0;
          row.records.forEach((record)=>{
               if(record.alignment_dmarc){
                 ++passCount;
               }else{
                      ++failCount;
               }

          })
          passData.push(passCount)
          failData.push(failCount)

   }
  
  var lineChartData = {
      labels  : dateLabels,
      datasets: [
        {
          label               : 'Pass',
          backgroundColor     : 'rgba(60,141,188,0.9)',
          borderColor         : 'rgba(60,141,188,0.8)',
          pointRadius          : false,
          pointColor          : '#3b8bba',
          pointStrokeColor    : 'rgba(60,141,188,1)',
          pointHighlightFill  : '#fff',
          pointHighlightStroke: 'rgba(60,141,188,1)',
          data                : passData
        },
        {
          label               : 'Fail',
          backgroundColor     : 'rgba(210, 214, 222, 1)',
          borderColor         : 'rgba(210, 214, 222, 1)',
          pointRadius         : false,
          pointColor          : 'rgba(210, 214, 222, 1)',
          pointStrokeColor    : '#c1c7d1',
          pointHighlightFill  : '#fff',
          pointHighlightStroke: 'rgba(220,220,220,1)',
          data                : failData
        },
      ]
    }

    let lineChartOptions = {
      maintainAspectRatio : false,
      responsive : true,
      legend: {
        display: true
      },
      scales: {
        xAxes: [{
          gridLines : {
            display : false,
          }
        }],
        yAxes: [{
          gridLines : {
            display : false,
          }
        }]
      }
    }



    var lineChartCanvas = $('#dmarc-conformance-chart').get(0).getContext('2d')
    lineChartData.datasets[0].fill = false;
    lineChartData.datasets[1].fill = false;
    lineChartOptions.datasetFill = false

    new Chart(lineChartCanvas, {
      type: 'line',
      data: lineChartData,
      options: lineChartOptions
    })
}


$.fn.ReviewDMARC = () => {
    let modalOptions = {
      keyboard: false,
      focus: true,
      backdrop: 'static'
    }

    $('#modal-content').html(`
    <div class="card card-primary" id="report-header">
      <div class= "card-header">
      <h3 class="card-title" id="report-title" >Review DMARC</h3>
                </div >
    <form id="dmarc-review-form">
      <div class="card-body">
        <div class="form-group">
          <label for="report-name-id">_DMARC</label>
          <input type="text" name="dmarc" class="form-control" id="dmarc-id" placeholder="Enter Your Domain here">
        </div>
      </div>
      <div class="card-footer">
        <div class="row">
            <div class="col-6" align="left">
                <button  id="upload-cancel-bttn" onclick="$.fn.cancelDialog()"  class="btn btn-secondary">Cancel</button>
            </div>
            <div class="col-6" align="right">
                <button id="dmarc-review-bttn" class="btn btn-primary">Submit</button>
            </div>
        </div>
      </div>
    </form>
    </div>`);
    $('#myModal').modal(modalOptions);
    $('#myModal').show();

}


$.fn.drawPieChart=(data)=>{

  let spfAlignmentCount = 0;
  let spfAlignmentFail = 0;
    
  let dkimAlignmentCount = 0;
  let dkimAlignmentFail = 0;
    
  let dmarcAlignmentCount = 0;
  let dmarcAlignmentFail = 0;

          data.forEach((record)=>{
             
            record.forEach((d)=>{
              
             if( typeof d.alignment_spf   == 'string' &&  d.alignment_spf ==="false"){
                spfAlignmentFail +=1
              }else if(typeof d.alignment_spf == 'string' && d.alignment_spf.toLowerCase()==="true"  ){
                  spfAlignmentCount +=1
              }else if(d.alignment_spf){
                spfAlignmentCount +=1

              }else{
                spfAlignmentFail+=1
              }
             if((typeof d.alignment_dkim == 'string' && d.alignment_dkim.toLowerCase()==="false") ){
                  dkimAlignmentFail+=1
               }else   if( (typeof d.alignment_dkim == 'string' && d.alignment_dkim.toLowerCase()==="true") ){
                dkimAlignmentCount+=1
             }else  if(d.alignment_dkim){
                dkimAlignmentCount+=1
               }else{
                  dkimAlignmentFail+=1
               }
                if((typeof d.alignment_dmarc == 'string' && d.alignment_dmarc.toLowerCase()==="false")){
                   dmarcAlignmentFail+=1
               }else  if( (typeof d.alignment_dmarc == 'string' &&  d.alignment_dmarc.toLowerCase()==="true")){
                dmarcAlignmentCount+=1
                }else if(d.alignment_dmarc){
                dmarcAlignmentCount+=1
               } else{
                  dmarcAlignmentFail+=1
               }

              })
         })

         $('#spf-piechart').html()
         $.fn.pieChart (spfAlignmentCount, spfAlignmentFail,'SPF','spf-piechart')
         $('#dkim-piechart').html()
         $.fn.pieChart (dkimAlignmentCount, dkimAlignmentFail,'DKIM','dkim-piechart')
         $('#dmarc-piechart').html()
         $.fn.pieChart (dmarcAlignmentCount, dmarcAlignmentFail,'DMARC','dmarc-piechart')
      
}

$.fn.pieChart= (alignmentCount,alignmentFail,protocol,chartID)=>{

 let   backgroundColor = []
  if (protocol == 'SPF'){
      backgroundColor =['#00a65a','#f56954']

  }else     if (protocol == 'DKIM'){
      backgroundColor =['#00c0ef','#f39c12']

  }else     if (protocol == 'DMARC'){
      backgroundColor =[ '#3c8dbc','#d2d6de']

  }


  var pieChartData        = {
      labels: [
          'Pass',
          'Fail'
      ],
      datasets: [
        {
          data: [alignmentCount,alignmentFail],
          backgroundColor : backgroundColor,
        }
      ]
    }
  
     var pieChartCanvas = $('#'+chartID).get(0).getContext('2d')
     var pieData        = pieChartData;
     var pieOptions     = {
       maintainAspectRatio : false,
       responsive : true,
          plugins: {
            legend: {
              position: 'top',
            },
            title: {
              display: true,
              text: protocol+' Alignment'
            }
          }
        }
   
     new Chart(pieChartCanvas, {
       type: 'pie',
       data: pieData,
       options: pieOptions
     })
   
}

$.fn.onlineDataFetch = (startDate,endDate,transDomain,mode)=>{
  let url =  `/api/dashboard/${startDate}/${endDate}/${transDomain}`
   $.ajax({ 
      url: url,
      dataType: 'json', 
      timeout: 500,    
      success: function (data,status,xhr) {  
          let pieData =[] 
            if($('#spf-piechart').is(":visible")){
                if (mode==1 || $.fn.checkForUpdates(window.dashboardData,data)){ 
                //  $.fn.showLoadingDialog('Updating...');
                //  window.isUpdateRunning = true;
                  window.dashboardData = data;
                  for (let row of data){ 
                      pieData.push(row.records.map((record)=>{
                          let temp_data = {};
                          temp_data['alignment_spf']=record.alignment_spf;
                          temp_data['alignment_dkim']=record.alignment_dkim;
                          temp_data['alignment_dmarc']=record.alignment_dmarc;
                          return temp_data;
                      })
                      )
                }
                $.fn.drawPieChart(pieData);
                $.fn.drawLineChart(data);
                $.fn.drawReportTable(data);
                
               // window.isUpdateRunning = false;
                }else{
                  //console.log("No dashboard data change observed")
                }
            }
          },
      error: function (jqXhr, textStatus, errorMessage) { // error callback 
          $('p').append('Error: ' + errorMessage);
      }
  });
  

}

$.fn.localDataFetch = (startDate,endDate,transDomain ,mode)=>{

  let recordSelect  = new Selector([{ 
    field: "table_name"
    ,value:"ReportMetadata"
    ,operator:Selector.EQ
  },{ 
    field:"report_metadata_begin_date"
    ,value:startDate
    ,operator:Selector.GTE
  },{ 
    field: "report_metadata_begin_date"
    ,value:endDate
    ,operator:Selector.LTE
  },{ 
    field: "policy_published_domain"
    ,value: `${transDomain}*`
    ,operator:Selector.REGEX
  }]
  
  )  
  
  $.fn.getPouchConnection().find({selector: recordSelect}).then((meta)=>{
     let promises           = [];
     let reportData         = [];
     //window.isUpdateRunning = true;
     let reportIDList = [];

     for (let result of meta['docs']){
        reportIDList.push(result.report_id);
     }
        
     
     let  reportSelect  = new Selector([{ 
                                          field: "table_name"
                                          ,value:"ReportRecords"
                                          ,operator:Selector.EQ
                                        },{ 
                                          field:"report_id"
                                          ,value:reportIDList
                                          ,operator:Selector.IN
                                        }
                                        ])

    
 $.fn.getPouchConnection().find({selector: reportSelect}).then((results) => {
   // console.log(results)
    let reportRecords = results['docs'];
    let metaRecords   = meta['docs'];

    let reportData = metaRecords.map((record)=>{
            let matchingRecords = reportRecords.filter((report)=>{
               return  report.report_id ==  record.report_id
            })
          return {...record, 'records':matchingRecords}
    })
    window.dashboardData = reportData
  meta =null;
  
  if($('#spf-piechart').is(":visible")){
   let pieData =[]
   let check =$.fn.checkForUpdates(window.dashboardData,reportData)


   if (mode==1 || check){ 
    // $.fn.showLoadingDialog('Updating...');
        for (let row of reportData){ 
          pieData.push(row.records.map((record)=>{
              let temp_data = {};
              temp_data['alignment_spf']=record.alignment_spf;
              temp_data['alignment_dkim']=record.alignment_dkim;
              temp_data['alignment_dmarc']=record.alignment_dmarc;
              return temp_data;
          })
          )
        }
        $.fn.drawPieChart(pieData);
        $.fn.drawLineChart(reportData);
        $.fn.drawReportTable(reportData);
        
    }
  }
  })
  
  
  })

}

$.fn.updateDashboard = (mode)=>{
 
  let startDate = $('#report-range-start').val().split(' ')[0]
  let endDate = $('#report-range-end').val().split(' ')[0]
  let domain = $('#dmarc-domain').val()
  let transDomain = domain=== "all"?".":domain;

  if (dashWorker) {
    dashWorker.postMessage([window.config,syncMode,startDate,endDate,transDomain]);
    dashWorker.onmessage = (event) => {
      let reportData  =event.data
      //console.log(reportData)
      if($('#spf-piechart').is(":visible")){
        let pieData =[]
        let check =$.fn.checkForUpdates(window.dashboardData,reportData)
     
     
        if (mode==1 || check){ 
             for (let row of reportData){ 
               pieData.push(row.records.map((record)=>{
                   let temp_data = {};
                   temp_data['alignment_spf']=record.alignment_spf;
                   temp_data['alignment_dkim']=record.alignment_dkim;
                   temp_data['alignment_dmarc']=record.alignment_dmarc;
                   return temp_data;
               })
               )
             }
             $.fn.drawPieChart(pieData);
             $.fn.drawLineChart(reportData);
             $.fn.drawReportTable(reportData);
             
         }
       }
       
    }
 
  }else{
    if (syncMode==='ONLINE'){
      $.fn.onlineDataFetch(startDate,endDate,transDomain, mode);
    }else if (syncMode==='LOCAL'){
      $.fn.localDataFetch(startDate,endDate,transDomain, mode);
    }
  }

  ;

 
}

$.fn.sortObject=(obj)=> {
  return Object.keys(obj).sort().reduce(function (result, key) {
      result[key] = obj[key];
      return result;
  }, {});
}


$.fn.checkForUpdates = (oldData, newData)=>{ 

	let dashDataUpdated = false;
	if (!oldData || (oldData.length != newData.length)){
	  	dashDataUpdated = true;
	}

	if(!dashDataUpdated){

		      for (let i in  oldData){
            let oldMetaRecords  = oldData[i]
  
            let newMetaRecords  = newData.filter((record)=> record['_id']==oldMetaRecords['_id'])
            if(newMetaRecords.length == 0){
              dashDataUpdated =true;
              break
            }else{
              newMetaRecords = newMetaRecords[0]
            }
            for( let k of Object.keys(oldMetaRecords)){
              //console.log(k)
             // console.log(oldMetaRecords[k])
             // console.log(newMetaRecords[k])
              if (k !== 'records' && oldMetaRecords[k].length >0 && oldMetaRecords[k] != newMetaRecords[k] ){
                dashDataUpdated = true;
                break;
              }else if (k == 'records'){
                    for(let j in oldMetaRecords[k]){
                       //console.log(j)
                      // console.log(oldMetaRecords[k][j])
                       let oldReportRecords = oldMetaRecords[k][j]

                       let newReportRecords = oldMetaRecords[k].filter((record)=> record['_id']==oldReportRecords['_id'])
                       if(newReportRecords.length== 0){
                            dashDataUpdated =True;
                            break
                       }else{

                        newReportRecords=newReportRecords[0]
                       }


                       for(let l of Object.keys(oldReportRecords)){
                          if(oldReportRecords[l]!==newReportRecords[l]){
                            dashDataUpdated = true;
                            break;
                          }

                       }
                        if(dashDataUpdated){
                          break;
                        }
                                    
                        }
        
        
        
              }


              if(dashDataUpdated){
                break;
              }
            }
            if(dashDataUpdated){
              break;
            }


		      }

	}
	return dashDataUpdated
}

$.fn.drawReportTable = (data)=>{
      let reportData = []
      for (let row of data){

         row.records.forEach((record)=>{
          let tempData = {};
          //console.log(record)
          tempData["from_domain"] = record.identifiers_header_from
          tempData["envelope_from"] = record.identifiers_envelope_from
          tempData["source_ip"] = record.source_ip_address
          tempData["source_ip_city"] = record.source_ip_city                                       
          tempData["source_ip_region"] = record.source_ip_region                                         
          tempData["source_ip_country"] = record.source_ip_country                                      
          tempData["source_ip_location"] = record.source_ip_location                                      
          tempData["source_ip_organization"] = record.source_ip_organization                                   
          tempData["source_ip_postal"] = record.source_ip_postal                                     
          tempData["source_ip_timezone"] = record.source_ip_timezone              
          tempData["ptr"]       = record.source_reverse_dns?record.source_reverse_dns:'';
          tempData["country"]   = record.source_country?record.source_country:'';
          tempData["volume"] = record.count
          tempData["policy_applied"] = record.policy_evaluated_disposition
          tempData["spf_dmarc"] = record.alignment_spf
          tempData["spf_raw"] = record.spf_result
          tempData["spf_mail_from"] = record.spf_domain
          tempData["dkim_dmarc"] = record.alignment_dmarc
          tempData["dkim_raw"] = record.alignment_dkim
          tempData["dkim_domain"] = record.dkim_domain?record.dkim_domain:'';
          tempData["dkim_selectors"] = record.dkim_selector?record.dkim_selector:'';
          tempData["reporter"] = row.report_metadata_org_name
          reportData.push(tempData)
         })

      }
      
      if ( $.fn.dataTable.isDataTable('#dmarc-report-table' ) ) {
        $('#dmarc-report-table').DataTable().destroy();
      }
      $('#dmarc-report-table').DataTable({
          "aaData": reportData,
          "columns": [
              {  
                  'orderable':      false,
                  'data':           null,
                  'defaultContent': ''
              },
              { "sTitle": "From Domain","data": "from_domain" },
              { "sTitle": "Envelope From","data": "envelope_from" },
              {"sTitle": "Source IP", "data": "source_ip" },
              {"sTitle": "IP City",   "data":  "source_ip_city" },
              {"sTitle": "IP Region",  "data": "source_ip_region" },
              {"sTitle": "IP Country", "data": "source_ip_country" },
              {"sTitle": "IP Location", "data": "source_ip_location" },
              {"sTitle": "IP Organisation", "data": "source_ip_organization" },
              {"sTitle": "IP Postal", "data": "source_ip_postal" },
              {"sTitle": "IP TimeZone", "data": "source_ip_timezone" },
              {"sTitle": "PTR", "data": "ptr" },
              {"sTitle": "Country", "data": "country" },
              {"sTitle": "Volume", "data": "volume" },
              {"sTitle": "Policy Applied", "data": "policy_applied" },
              {"sTitle": "SPF DMARC", "data": "spf_dmarc" },
              {"sTitle": "SPF Raw", "data": "spf_raw" },
              {"sTitle": "SPF Mail From", "data": "spf_mail_from" },
              { "sTitle": "DKIM DMARC","data": "dkim_dmarc" },
              { "sTitle": "DKIM Raq","data": "dkim_raw" },
              { "sTitle": "DKIM Domain","data": "dkim_domain" },
              { "sTitle": "DKIM Selectors","data": "dkim_selectors" },
              { "sTitle": "Reporter","data": "reporter" }
          ],
        "paging": true,
        "lengthChange": true,
        "searching": true,
        "ordering": true,
        "info": false,
        "autoWidth": true,
        "responsive": true,
        //"buttons": ["copy", "csv", "excel", "pdf", "print", "colvis"],
        "buttons": ["copy", "csv", "excel", "pdf", "print"],
        
      }).buttons().container().appendTo('#dmarc-report-table_wrapper .col-md-6:eq(0)');
     // $.fn.closeDialog();
      //window.isUpdateRunning = false;


}


$.fn.loadSetup=()=>{

  clearInterval(window.dashboardUpdateID);
  //window.isUpdateRunning = false;
 // if (  DisplayManager.pageUpdateHistory.has('setup')==0){
      let  sNavItems        = {...window.defaultComponents.sidebar.sidebarNav.sidebarNavItems,sidebarNavItemList:[{
        "itemClass":"nav-item",   
       "href": "#",
       "navLinkClass":"nav-link",
       "itemIconClass": "nav-icon fas fa-mail-bulk",
       "text": "Mailboxes",
       "spanClass": "",
       "spanText": "",
       "position": 0
       ,"actions":{"event":"onClick", "functionName":"$.fn.showMailboxes()", "parameters":{}}
       ,"subNavItemList": [{
                             "navAnchorClass":"nav-link active",
                            "href": "#",
                            "itemIconClass": "far fa-table nav-icon",
                            "text": "Mailboxes"
                            ,"actions":{"event":"onClick", "functionName":"$.fn.showMailboxes()", "parameters":{}}
                        }, {
                            "href": "#",
                            "itemIconClass": "fas fa-envelope-open nav-icon",
                            "text": "New IMAP Account"
                            ,"actions":{"event":"onClick", "functionName":"$.fn.editMailBox()", "parameters":{}}
                        }, {
                          "href": "#",
                          "itemIconClass": "fas fa-envelope-open-text nav-icon",
                          "text": "New Gmail Account"
                          ,"actions":{"event":"onClick", "functionName":"$.fn.editGmailBox()", "parameters":{}}
                      }

                    ]
       
           },{
               "itemClass":"nav-item",   
              "href": "#",
              "navLinkClass":"nav-link",
              "itemIconClass": "fas fa-clipboard-list nav-icon",
              "text": "Schedules",
              "spanClass": "",
              "spanText": "",
              "position": 1
              ,"actions":{"event":"onClick", "functionName":"$.fn.showSchedules()", "parameters":{}}
              ,"subNavItemList": [{
                      "navAnchorClass":"nav-link active",
                      "href": "#",
                      "itemIconClass": "fa-solid fa-calendar-days nav-icon",
                      "text": "Schedules"
                      ,"actions":{"event":"onClick", "functionName":"$.fn.showSchedules()", "parameters":{}}
                      }, {
                      "href": "#",
                      "itemIconClass": "fas fa-clock nav-icon",
                      "text": "New Schedule"
                      ,"actions":{"event":"onClick", "functionName":"$.fn.editSchedule()", "parameters":{}}
                      }
                      ]
                    },{
                      "itemClass":"nav-item",   
                    "href": "#",
                    "navLinkClass":"nav-link",
                    "itemIconClass": "fas fa-envelope-open nav-icon",
                    "text": "Emails",
                    "spanClass": "",
                    "spanText": "",
                    "position": 2
                    ,"actions":{"event":"onClick", "functionName":"$.fn.showReportEmails()", "parameters":{}}
                      },{
                  "itemClass":"nav-item",   
                  "href": "#",
                  "navLinkClass":"nav-link",
                  "itemIconClass": "fas fa-upload nav-icon",
                  "text": "Uploads",
                  "spanClass": "",
                  "spanText": "",
                  "position": 3
                  ,"actions":{"event":"onClick", "functionName":"$.fn.showReportUploads()", "parameters":{}}
                  },{
                  "itemClass":"nav-item",   
                  "href": "#",
                  "navLinkClass":"nav-link",
                  "itemIconClass": "fas fa-th nav-icon",
                  "text": "Report Metadata",
                  "spanClass": "",
                  "spanText": "",
                  "position": 4
                  ,"actions":{"event":"onClick", "functionName":"$.fn.showReportMetadata()", "parameters":{}}
                  },{
                  "itemClass":"nav-item",   
                  "href": "#",
                  "navLinkClass":"nav-link",
                  "itemIconClass": "fas fa-th-list nav-icon",
                  "text": "Report Records",
                  "spanClass": "",
                  "spanText": "",
                  "position": 5
                  ,"actions":{"event":"onClick", "functionName":"$.fn.showReportRecords()", "parameters":{}}
                  },{
                    "itemClass":"nav-item",   
                  "href": "#",
                  "navLinkClass":"nav-link",
                  "itemIconClass": "nav-icon fas fa-bolt",
                  "text": "Jobs",
                  "spanClass": "",
                  "spanText": "",
                  "position": 6
                  ,"actions":{"event":"onClick", "functionName":"$.fn.showJobs()", "parameters":{}}

            } ]};
      const siderbarNav    = {...window.defaultComponents.sidebar.sidebarNav,sidebarNavItems: sNavItems}
      DisplayManager.updateComponentDisplay(Sidebar, {...window.defaultComponents.sidebar,sidebarNav: siderbarNav});
      ;
      let setupContentWrapper= { ...window.defaultComponents.contentHeader.contentWrapper,contentRows:[{"htmlText":( DashboardTable({"statsTitle":"GMail Accounts","statsIcon":"fa fa-envelope", "tableData":[],"id":"gmail-accounts"}))},{"htmlText":( DashboardTable({"statsTitle":"IMAP Accounts","statsIcon":"fa fa-envelope", "tableData":[],"id":"imap-accounts"}))}],dashboardReportRange:{} } 
      //console.log(setupContentWrapper)
      DisplayManager.updateComponentDisplay(ContentHeader,  {...window.defaultComponents.contentHeader,parentPage :"Setup",pageTitle : "Mailboxes", contentWrapper: setupContentWrapper});
      //DisplayManager.display('setup');
      $.fn.showMailboxes();
      
  //}
}


$.fn.loadDashboard=()=>{

 if ( !DisplayManager.pageUpdateHistory.has('dashboard')){

      DisplayManager.addComponentDisplay(Preloader, window.defaultComponents.preloader);
      DisplayManager.addComponentDisplay(Navbar, window.defaultComponents.navbar);
      DisplayManager.addComponentDisplay(Sidebar, window.defaultComponents.sidebar);
      DisplayManager.addComponentDisplay(ContentHeader, window.defaultComponents.contentHeader);
      DisplayManager.addComponentDisplay(Footer, {});
      DisplayManager.display('dashboard');

  }else{
   
    DisplayManager.updateComponentDisplay(Sidebar, window.defaultComponents.sidebar);
    DisplayManager.updateComponentDisplay(ContentHeader,window.defaultComponents.contentHeader );

  }
    

  if(window.defaultComponents.dashboardData.length > 0){
    window.dashboardData = window.defaultComponents.dashboardData;
  if($('#spf-piechart').is(":visible")){
    let pieData =[];
    let dmarcDomains = new Set();
    dmarcDomains.add('all')
    for (let row of  window.dashboardData){ 
          dmarcDomains.add(row['policy_published_domain'])
            pieData.push(row.records.map((record)=>{
            let  temp_data = {};
            temp_data['alignment_spf']=record.alignment_spf;
            temp_data['alignment_dkim']=record.alignment_dkim;
            temp_data['alignment_dmarc']=record.alignment_dmarc;
            return temp_data;
        })
        )
      }
      $.fn.drawPieChart(pieData);
      $.fn.drawLineChart(window.dashboardData );
      $.fn.drawReportTable(window.dashboardData );

    $('#daterange-btn').daterangepicker({
      ranges   : {
        'Today'       : [moment(), moment()],
        'Yesterday'   : [moment().subtract(1, 'days'), moment().subtract(1, 'days')],
        'Last 7 Days' : [moment().subtract(6, 'days'), moment()],
        'Last 30 Days': [moment().subtract(29, 'days'), moment()],
        'This Month'  : [moment().startOf('month'), moment().endOf('month')],
        'Last Month'  : [moment().subtract(1, 'month').startOf('month'), moment().subtract(1, 'month').endOf('month')]
      },
      startDate: moment().subtract(29, 'days'),
      endDate  : moment()
    },
    function (start, end) {
      $('#report-range-start').val(start.format('YYYY-MM-DD'))
      $('#report-range-end').val(end.format('YYYY-MM-DD'))
      $('#reportrange span').html(start.format('YYYY-MM-DD') + ' - ' + end.format('YYYY-MM-DD'))
      clearInterval(window.dashboardUpdateID);
      $.fn.updateDashboard(1);
     window.dashboardUpdateID = setInterval(() => {$.fn.updateDashboard(0)},syncInterval);
      
    }
    )
    $('#dmarc-domain') .find('option').remove().end()
    for (let domain of dmarcDomains){
        $('#dmarc-domain').append(`<option value="${domain}">${domain}</option>`);
    }

    $('#dmarc-domain').on('change', (e)=>{ 
      clearInterval(window.dashboardUpdateID);
      $.fn.updateDashboard(1);
      window.dashboardUpdateID = setInterval(() => {$.fn.updateDashboard(0)},syncInterval);
     })
     clearInterval(window.dashboardUpdateID)
     window.dashboardUpdateID = setInterval(() => {$.fn.updateDashboard(0)},syncInterval);
    }
  }else{
      clearInterval(window.dashboardUpdateID);
      $.fn.updateDashboard(1);
      if($('#spf-piechart').is(":visible")){
        let pieData =[];
        let dmarcDomains = new Set();
        dmarcDomains.add('all')
        window.dashboardData = window.defaultComponents.dashboardData
        for (let row of  window.dashboardData){ 
                dmarcDomains.add(row['policy_published_domain'])
                pieData.push(row.records.map((record)=>{
                let  temp_data = {};
                temp_data['alignment_spf']=record.alignment_spf;
                temp_data['alignment_dkim']=record.alignment_dkim;
                temp_data['alignment_dmarc']=record.alignment_dmarc;
                return temp_data;
            })
            )
          }
          $.fn.drawPieChart(pieData);
          $.fn.drawLineChart(window.dashboardData );
          $.fn.drawReportTable(window.dashboardData );
    
        $('#daterange-btn').daterangepicker({
          ranges   : {
            'Today'       : [moment(), moment()],
            'Yesterday'   : [moment().subtract(1, 'days'), moment().subtract(1, 'days')],
            'Last 7 Days' : [moment().subtract(6, 'days'), moment()],
            'Last 30 Days': [moment().subtract(29, 'days'), moment()],
            'This Month'  : [moment().startOf('month'), moment().endOf('month')],
            'Last Month'  : [moment().subtract(1, 'month').startOf('month'), moment().subtract(1, 'month').endOf('month')]
          },
          startDate: moment().subtract(29, 'days'),
          endDate  : moment()
        },
        function (start, end) {
          $('#report-range-start').val(start.format('YYYY-MM-DD'))
          $('#report-range-end').val(end.format('YYYY-MM-DD'))
          $('#reportrange span').html(start.format('YYYY-MM-DD') + ' - ' + end.format('YYYY-MM-DD'))
          clearInterval(window.dashboardUpdateID);
          $.fn.updateDashboard(1);
         window.dashboardUpdateID = setInterval(() => {$.fn.updateDashboard(0)},syncInterval);
          
        }
        )
        $('#dmarc-domain') .find('option').remove().end()
        //console.log(dmarcDomains)
        for (let domain of dmarcDomains){
            $('#dmarc-domain').append(`<option value="${domain}">${domain}</option>`);
        }
    
        $('#dmarc-domain').on('change', (e)=>{ 
          clearInterval(window.dashboardUpdateID);
          $.fn.updateDashboard(1);
          window.dashboardUpdateID = setInterval(() => {$.fn.updateDashboard(0)},syncInterval);
         })
         clearInterval(window.dashboardUpdateID)
         window.dashboardUpdateID = setInterval(() => {$.fn.updateDashboard(0)},syncInterval);
        }
  }
}

$("#index-root").ready((e) => {
  
    DisplayManager.setCurrentPageID("index-root");
    $.fn.loadDashboard();

})

$.fn.capitalize = (str)=>{
  return  str.charAt(0).toUpperCase() + str.slice(1);
}

$.fn.loadBuildDMARC=()=>{

  clearInterval(window.dashboardUpdateID);

      let  sNavItems        = {...window.defaultComponents.sidebar.sidebarNav.sidebarNavItems,sidebarNavItemList:[{
        "itemClass":"nav-item",   
       "href": "#",
       "navLinkClass":"nav-link",
       "itemIconClass": "nav-icon fas fa-cogs",
       "text": "Configure Dmarc",
       "spanClass": "",
       "spanText": "",
       "position": 0
       ,"actions":{"event":"onClick", "functionName":"$.fn.loadBuildDMARC()", "parameters":{}}
           } ,{
        "itemClass":"nav-item",   
       "href": "#",
       "navLinkClass":"nav-link",
       "itemIconClass": "nav-icon fas fa-history",
       "text": "Dmarc Records",
       "spanClass": "",
       "spanText": "",
       "position": 1
       ,"actions":{"event":"onClick", "functionName":"$.fn.showDmarcRecords()", "parameters":{}}
       
           } ]};
      const siderbarNav    = {...window.defaultComponents.sidebar.sidebarNav,sidebarNavItems: sNavItems}
      DisplayManager.updateComponentDisplay(Sidebar, {...window.defaultComponents.sidebar,sidebarNav: siderbarNav});
      const indentation = "&nbsp;&nbsp;"
      let buildRow1 = `  
              <div class="col-md-3"><label for="dmarc-domain-name-id">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Domain&nbsp;(Host Name)</label></div>
              <div class="col-md-6"><input type="text" name="dmarc_domain_name"  class="form-control" id="dmarc-domain-name-id" placeholder="domain.com">  </div>
              
             `
      let buildRow2 = `
        <div class="form-group col-md-6 mt-4">   
         <p class="h2 mt-2 mb-4">Configure a DMARC Record</p>
         <hr>
         <div>
      
          <div> 
             <div class="mt-4"><strong>1. How do you want your domain  emails that fail authentication to be treated?</strong></div>         
             <div><select class="form-control select2 mt-4" id="domain-emails"><option value="null" selected="selected">---</option> <option value="None" >None</option> <option value="Quarantine">Quarantine</option>  <option value="Reject">Reject</option>  </select> </div>
            
          </div>

          <div id="subdomain-check"> 
             <div class="mt-4"><strong>2. Do you want this policy to cover your subdomain?</strong></div>
             <div><select class="form-control select2 mt-4" id="sub-domain-cover"><option value="no" selected="selected">No</option> <option value="yes">Yes</option>  </select> </div>
             
          </div>

          <div id="subdomain-emails" style="display:none"> 
          <div class="mt-2"><strong> <span id="subdomain-emails-index">3</span>. How do you want your subdomain emails to be treated?</strong></div>
        
          <div><select class="form-control select2 mt-4" id="subdomain-emails-text"> <option value="null" selected="selected">---</option><option value="None" >None</option> <option value="Quarantine">Quarantine</option>  <option value="Reject">Reject</option>  </select> </div>
         
       </div>
          
          <div> 
             <div class="mt-4"><strong><span id="rua-emails-index">3</span>. Which address would you have your aggregate report (RUA) sent to?</strong></div>
             <div><input type="text" name="rua_target_email_address"  class="form-control mt-4" id="rua-target-email-address-id" placeholder="ruatarget@domain.com"> </div>
          </div>

       <div> 
          <div class="mt-4"><strong><span id="ruf-emails-index">4</span>. Which address would you have your forensic report (RUF) sent to?</strong></div>
       
          <div><input type="text" name="ruf_target_email_address"  class="form-control mt-4" id="ruf-target-email-address-id" placeholder="ruftarget@domain.com"> </div>
        
       </div>

       <div> 
       <div class="mt-4"> <strong><span id="frequency-index">5</span>.How frequently do you want to receive reports?</strong></div>
       
       <div><input type="text" name="email_frequency"  class="form-control mt-4" id="email-frequency" placeholder="360 -> 86400"> </div>
    
    </div>
        </div>
              </div>
              <div class="form-group col-md-6">
              <p>&nbsp;</p>
              <p>&nbsp;</p>
                    <label>DMARC Record</label>
                    <textarea class="form-control" id="dmarc-record-text" rows="4" placeholder="DMARC" disabled="" style="resize: none;"></textarea>
                    <div class="row float-right mt-4"><div class="col-md"><button  class="btn btn-primary" id="dmarc-copy-btn" >Copy</button></div>
                    <div class="col-md"><button type="submit" class="btn btn-success" id="dmarc-save-btn" >Save</button></div> </div>
              </div>
        
`;       
      let dmarcBuildContentWrapper= { ...window.defaultComponents.contentHeader.contentWrapper,contentRows:[{htmlText:buildRow1,rowClass:'input-group input-group-lg'},{htmlText:buildRow2}],dashboardReportRange:{} } 
      //console.log(dmarcBuildContentWrapper)
      DisplayManager.updateComponentDisplay(ContentHeader,  {...window.defaultComponents.contentHeader,parentPage :"Build",pageTitle : "Configure DMARC", contentWrapper: dmarcBuildContentWrapper});
      //DisplayManager.display('setup');
    $('#domain-emails, #subdomain-emails').attr("title",`None - should only be used for testing purposes as it does not offer any protection against spoofing and phising\nQuarantine - informs the recipient organization to send the received mail but with some element of risk\nReject - provides the best security`)

    $('#email-frequency').attr('title','The more frequently reports are received, the better as this helps your team uncover threats in a timely fashion ')

    $('#rua-target-email-address-id, #ruf-target-email-address-id').attr('title','If adding multiple email addresses, please use a comma to separate each one')

    $('#domain-emails, #subdomain-emails, #rua-target-email-address-id, #ruf-target-email-address-id, #email-frequency').on('change', ()=> {$.fn.updateDMARCText()})
    $('#sub-domain-cover').change((e)=>{

        let value = e.target.value;
        if(value.toLowerCase()=='yes'){
              $('#subdomain-emails').show()
              $('#rua-emails-index').html('4')
              $('#ruf-emails-index').html('5')
              $('#frequency-index').html('6')
        }else{
          $('#subdomain-emails').hide()
          $('#rua-emails-index').html('3')
          $('#ruf-emails-index').html('4')
          $('#frequency-index').html('5')

        }

        $.fn.updateDMARCText();
    })
    $('#dmarc-copy-btn').on('click', (e)=>{  
      let val = $('#dmarc-record-text').val()
      if (!val || val.length == 0 ){
           $.fn.showAlert('No DMARC Record to copy', 'danger');
      }else{ 
          navigator.clipboard.writeText( $('#dmarc-record-text').val());
          $.fn.showAlert('DMARC Record copied to clipboard', 'success');
      }
    } )
 
    $('#email-frequency').on('change', (e)=>{
             let repeat =  e.target.value;
             repeat = repeat.trim()
            if(repeat && repeat.length > 0 && !isNaN(parseInt(repeat)) ){
               repeat = parseInt(repeat);

                if(repeat< 360 || repeat > 86400){

                        $.fn.showAlert('Interval not in the accepted range','danger')

                        let classList =  $('#email-frequency').attr('class')
                        if (classList.indexOf('is-invalid')< 0){
                           $('#email-frequency').addClass('is-invalid')
                           $('#dmarc-save-btn').attr('disabled','disabled')
                        }
                }else{
                  let classList =  $('#email-frequency').attr('class')
                  if (classList.indexOf('is-invalid')> -1){
                     $('#email-frequency').removeClass('is-invalid')
                  }
                  $('#dmarc-save-btn').removeAttr('disabled')
                }
             }else if (repeat && repeat.length > 0 &&  isNaN(parseInt(repeat)) ){
                    let classList =  $('#email-frequency').attr('class')
                    if (classList.indexOf('is-invalid')< 0){
                      $('#email-frequency').addClass('is-invalid')
                    }
                    $('#dmarc-save-btn').attr('disabled','disabled')
                  $.fn.showAlert('Interval not in the accepted format','danger')
             }
         
    })

    $('#dmarc-save-btn').on('click', (e)=>{

       e.preventDefault();

       let domain = $('#dmarc-domain-name-id').val()
       domain = domain? domain.trim():'';
       let dmarcRecord =  $('#dmarc-record-text').val()
       dmarcRecord = dmarcRecord?dmarcRecord.trim(): '';


       if(!domain || domain.length==0 ){
          let classList =  $('#dmarc-domain-name-id').attr('class')
          if (classList.indexOf('is-invalid')< 0){
              $('#dmarc-domain-name-id').addClass('is-invalid')
          }

       }

       if(!dmarcRecord ||dmarcRecord.length==0 ){
            $.fn.showAlert('No record to save', 'danger')
            return
       }else{
            let p = $('#domain-emails').val() && $('#domain-emails').val()!= "null" ?  $('#domain-emails').val().trim().toLowerCase():null
            p  = p?` p=${p}; `:``
            let rua   =   $('#rua-target-email-address-id').val()
            let ruf   =   $('#ruf-target-email-address-id').val()?$('#ruf-target-email-address-id').val():null
            rua       =   rua  && rua.length> 0?` rua=mailto:${rua};`:``;
            ruf       =   ruf && ruf.length> 0?` ruf=mailto:${ruf};`:``;
            let sp    =   $('#sub-domain-cover').val()=="yes" && $('#subdomain-emails-text').val()!= "null" ?$('#subdomain-emails-text').val().trim().toLowerCase():null
            sp        =   sp?` sp=${sp};`:``
            let reportInterval = $('#email-frequency').val()?$('#email-frequency').val():null;
            let ri = reportInterval?` ri=${reportInterval} `:''
        let formData = new FormData()
        formData.append("mode","new");
        formData.append("domain_name", domain);
        formData.append("p", p ); 
        formData.append("rua", rua);
        formData.append("ruf", ruf); 
        formData.append("sp", sp);  
        formData.append("ri", ri);  
        formData.append("dmarc_txt", dmarcRecord);  
        
         $.ajax({
                url: "/api/add/dmarc",
                type: "POST",
                data: formData,
                processData: false,
                processData: false,
                contentType: false,
                crossDomain: true,
                success:  (result)=> {
                    new Promise( (resolve)=>{
                     resolve( $.fn.resetModal())
                    }).then(()=>{
                      let resultClass = result.message.toLowerCase().indexOf('success') >-1?'success':'danger'
                      $.fn.showAlert(result.message,resultClass) 
                    })
                },
                error: (e)=>{
        
                  new Promise( (resolve)=>{
                    resolve( $.fn.resetModal())
                   }).then(()=>{
                    
                     $.fn.showAlert('DMARC Record could not be saved','danger') 
                   })
        
                }
            })
       }
    })

    $('#dmarc-domain-name-id').on('change', (e)=>{
      let policy = $('#domain-emails').val() && $('#domain-emails').val()!= "null" ?  $('#domain-emails').val().trim().toLowerCase():null
      policy  = policy?` p=${policy}; `:``
      let rua    = $('#rua-target-email-address-id').val()
      rua   = rua  && rua.length> 0?` rua=mailto:${rua};`:``;
      let ruf   = $('#ruf-target-email-address-id').val()?$('#ruf-target-email-address-id').val():null
      ruf  = ruf && ruf.length> 0?` ruf=mailto:${ruf};`:``;
      let subPolicy = $('#sub-domain-cover').val()=="yes" && $('#subdomain-emails-text').val()!= "null" ?$('#subdomain-emails-text').val().trim().toLowerCase():null
      subPolicy =subPolicy?` sp=${subPolicy};`:``
      let reportInterval = $('#email-frequency').val()?$('#email-frequency').val():null;
      let ri = reportInterval?` ri=${reportInterval} `:''

      if(policy.length> 0 || rua.length> 0 ||ruf.length > 0 || subPolicy.length > 0 || ri.length > 0 ){

        $.fn.updateDMARCText();
      }

    })

}

$.fn.updateDMARCText=()=>{

  let dmarcRecordText =[]
  
  let hostName = $('#dmarc-domain-name-id').val().trim()
  if(hostName){ 
        dmarcRecordText.push(`Type: TXT`);
        dmarcRecordText.push(`Host/Name:  _DMARC.${hostName}`)
        let policy = $('#domain-emails').val() && $('#domain-emails').val()!= "null" ?  $('#domain-emails').val().trim().toLowerCase():null
        policy  = policy?` p=${policy}; `:``
        let rua    = $('#rua-target-email-address-id').val()
        rua   = rua  && rua.length> 0?` rua=mailto:${rua};`:``;
        let ruf   = $('#ruf-target-email-address-id').val()?$('#ruf-target-email-address-id').val():null
        ruf  = ruf && ruf.length> 0?` ruf=mailto:${ruf};`:``;
        let subPolicy = $('#sub-domain-cover').val()=="yes" && $('#subdomain-emails-text').val()!= "null" ?$('#subdomain-emails-text').val().trim().toLowerCase():null
        subPolicy =subPolicy?` sp=${subPolicy};`:``
        let reportInterval = $('#email-frequency').val()?$('#email-frequency').val():null;
        let ri = reportInterval?` ri=${reportInterval} `:''
        let valueTemplate =  `Value: v=DMARC1;${policy}${rua}${ruf}${subPolicy}${ri}`
        dmarcRecordText.push(valueTemplate)

  }
  $('#dmarc-record-text').val(dmarcRecordText.join(`\n`))


}

$.fn.loadReviewDMARC = () => {
  clearInterval(window.dashboardUpdateID);
  
        let  sNavItems        = {...window.defaultComponents.sidebar.sidebarNav.sidebarNavItems,sidebarNavItemList:[]};
        const siderbarNav    = {...window.defaultComponents.sidebar.sidebarNav,sidebarNavItems: sNavItems}
        DisplayManager.updateComponentDisplay(Sidebar, {...window.defaultComponents.sidebar,sidebarNav: siderbarNav});
        const indentation = "&nbsp;&nbsp;"
  
        let buildRow1= `
          <div class="form-group col-md-6">   
    <div class="card card-primary" id="report-header">
        <div class= "card-header">
        <h3 class="card-title" id="report-title" >Review DMARC Record for Domain</h3>
                  </div >
      <form id="dmarc-review-form">
        <div class="card-body">
          <div class="form-group">
            <label for="report-name-id">_DMARC</label>
            <input type="text" name="dmarc" class="form-control" id="dmarc-id" placeholder="Enter Your Domain here">
          </div>
        </div>
        <div class="card-footer">
          <div class="row">
              <div class="col-6" align="left">
                  &nbsp;
              </div>
              <div class="col-6" align="right">
                  <button id="dmarc-review-bttn" class="btn btn-primary">Submit</button>
              </div>
          </div>
        </div>
      </form>
      </div>
                </div>
                <div class="form-group col-md-6">
       
                      <label>Output</label>
                      <textarea class="form-control" id="dmarc-review-output" rows="8" placeholder="" disabled="" style="resize: none;"></textarea>
                      
                </div> `;       
        let dmarcBuildContentWrapper= { ...window.defaultComponents.contentHeader.contentWrapper,contentRows:[{htmlText:buildRow1,rowClass:'input-group input-group-lg'}],dashboardReportRange:{} } 
        DisplayManager.updateComponentDisplay(ContentHeader,  {...window.defaultComponents.contentHeader,parentPage :"Review",pageTitle : "Check DMARC", contentWrapper: dmarcBuildContentWrapper});


        $('#dmarc-review-bttn').on('click', (e)=>{
            e.preventDefault()
           let domainName =   $('#dmarc-id').val()
           if(!domainName || domainName.length==0){

            let classList =   $('#dmarc-id').attr('class')
            if (classList.indexOf('is-invalid')< 0){
              $('#dmarc-id').addClass('is-invalid')
            }

        }else{
               let classList =  $('#dmarc-id').attr('class')
              if (classList.indexOf('is-invalid')> -1){
                $('#dmarc-id').removeClass('is-invalid')
              }

              let formData = new FormData()
              formData.append('domain_name',domainName)
              $.ajax({
                url: "/api/checkdmarc",
                type: "POST",
                data: formData,
                processData: false,
                processData: false,
                contentType: false,
                crossDomain: true,
                success:  (result)=> {
                  if(result && result.message){

                    $('#dmarc-review-output').val(JSON.stringify(result.message))
                   }
                  
                    new Promise( (resolve)=>{
                     resolve( $.fn.resetModal())
                    }).then(()=>{
                    
                      $.fn.showAlert(domainName+'DMARC review complete','success') 
                    })
                },
                error: (e)=>{
            
                  new Promise( (resolve)=>{
                    resolve( $.fn.resetModal())
                   }).then(()=>{
                    
                     $.fn.showAlert('IDMARC review Failed','danger','$.fn.showMailboxes()') 
                   })
            
                }
            })

           }

        })
  
  
      }
  
$.fn.removeGmailAccount  = (id=-1)=> {
  const formData = new FormData();
  formData.append("account_id", id);
  $.ajax({
    url: "/api/delete/GMailAccounts",
    type: "POST",
    data: formData,
    processData: false,
    processData: false,
    contentType: false,
    crossDomain: true,
    success:  (result)=> {
        new Promise( (resolve)=>{
         resolve( $.fn.resetModal())
        }).then(()=>{
          let resultClass = result.message.toLowerCase().indexOf('success') >-1?'success':'danger'
          $.fn.showAlert(result.message,resultClass,'$.fn.showMailboxes()') 
        })
    },
    error: (e)=>{

      new Promise( (resolve)=>{
        resolve( $.fn.resetModal())
       }).then(()=>{
        
         $.fn.showAlert('IMAP Account Removal Failed','danger','$.fn.showMailboxes()') 
       })

    }
})


}


$.fn.removeIMAPAccount = (id=-1)=> {
  const formData = new FormData();
  formData.append("account_id", id);
  $.ajax({
    url: "/api/delete/IMAPAccounts",
    type: "POST",
    data: formData,
    processData: false,
    processData: false,
    contentType: false,
    crossDomain: true,
    success:  (result)=> {
        new Promise( (resolve)=>{
         resolve( $.fn.resetModal())
        }).then(()=>{
          let resultClass = result.message.toLowerCase().indexOf('success') >-1?'success':'danger'
          $.fn.showAlert(result.message,resultClass, 'success','$.fn.showMailboxes()') 
        })
       // 
    },
    error: (e)=>{

      new Promise( (resolve)=>{
        resolve( $.fn.resetModal())
       }).then(()=>{
        
         $.fn.showAlert('IMAP Account Removal Failed','danger','$.fn.showMailboxes()') 
       })

    }
})


}

$.fn.removeSchedule  = (id=-1)=> {
  const formData = new FormData();
  formData.append("schedule_id", id);
  $.ajax({
    url: "/api/delete/GMailAccounts",
    type: "POST",
    data: formData,
    processData: false,
    processData: false,
    contentType: false,
    crossDomain: true,
    success:  (result)=> {
        new Promise( (resolve)=>{
         resolve( $.fn.resetModal())
        }).then(()=>{
          let resultClass = result.message.toLowerCase().indexOf('success') >-1?'success':'danger'
          $.fn.showAlert(result.message,resultClass,'$.fn.showSchedules()') 
        })
       
    },
    error: (e)=>{

      new Promise( (resolve)=>{
        resolve( $.fn.resetModal())
       }).then(()=>{
        
         $.fn.showAlert('IMAP Account Removal Failed','danger','$.fn.showSchedules()') 
       })

    }
})


}


$.fn.editMailBox = (query='none')=>{
  let recordSelect  = new Selector([{ 
    field: "table_name"
    ,value:"Schedules"
    ,operator:Selector.EQ
  },{ 
    field: "scheduleStatus"
    ,value:1
    ,operator:Selector.EQ
  }]
  )
  $.fn.getPouchConnection().find({selector: recordSelect}).then((meta)=>{
  let results =   meta['docs'];
  return results.map((result)=>{
    return `<option value="${result.schedule_id}">${result.name}</option>`
  })

}).then((schedules) =>{
  
  $.ajax({
    url: "/api/data/IMAPAccounts?imapaccounts="+JSON.stringify(query),
    type: "GET",
    processData: false,
    contentType: false,
    crossDomain: true,
    success:  (results)=> {
	   return   new Promise((resolve)=>{
      let imapAccount = results['imapaccounts']
         resolve(imapAccount)
       })
    },
    error: (e)=>{

     

    }
}
).then((record)=>{

   
  record = record && Object.keys(record).length==1?record['imapaccounts'][0]:null
  let titlePrefix = record?'Edit':'New'
  let button  = record?'Update':'Add'
  $('.page-title').text(titlePrefix+' IMAP Account')

  $('#contentwrapper-node').html(
    `<div class="container-fluid"><div class="row">       
     <div class="card card-primary col-md-12 w-100">
    <div class="card-header">
      <h3 class="card-title">${titlePrefix} IMAP Mail Server</h3>
    </div>
    <form class="form-horizontal">
      <div class="card-body">
        <div class="form-group row">
          <label for="imap-server-address" class="col-sm-2 col-form-label">IMAP Server</label>
          <div class="col-sm-10">
            <input type="text" class="form-control" name="imap_server_address" id="imap-server-address" value="${record?.imap_server_address?record.imap_server_address:''}" placeholder="IMAP Server Address">
          </div>
        </div>
        <div class="form-group row">
        <label for="imap-port" class="col-sm-2 col-form-label">Port</label>
        <div class="col-sm-10">
          <input type="imap_port" class="form-control"  id="imap-port" value="${record?.imap_port?record.imap_port:''}"  placeholder="port">
        </div>
      </div>
      <div class="form-group row">
          <label for="imap-username" class="col-sm-2 col-form-label" >Username</label>
          <div class="col-sm-10">
            <input type="imap_username" class="form-control"  id="imap-username"  value="${record?.imap_username?record.imap_username:''}"  placeholder="Username">
          </div>
        </div>
        <div class="form-group row">
          <label for="imap-password" class="col-sm-2 col-form-label">Password</label>
          <div class="col-sm-10">
            <input  type="password" class="form-control" id="imap-password" value="${record?.imap_password?record.imap_password:''}"  placeholder="Password">
          </div>
        </div>
        <div class="form-group row">
          <label for="imap-confirm-password" class="col-sm-2 col-form-label">Password</label>
          <div class="col-sm-10">
            <input  type="password" class="form-control" id="imap-confirm-password" value="${record?.imap_password?record.imap_password:''}" placeholder="Confirm Password">
          </div>
        </div>
        <div class="form-group row">
        <div class="col-md-3"><label>Security</label></div>
        <div class="col-md-9"> <select name="imap_security" id="imap-security" class="form-control select2" style="width: 100%;">
            <option selected="selected">None</option>
            <option>None</option>
            <option>TLS</option>
            <option>SSL</option>
          </select></div>
      </div>
      <div class="form-group row">
       <div class="col-md-3"><label>Report Schedule</label></div>
       <div class="col-md-9"><select  name="imap_report_schedule" id="imap-report-schedule" class="form-control select2" style="width: 100%;">
        <option selected="selected">None</option>
      ${schedules.join('')}
      </select>
      </div>
  </div>
      </div>
      <div class="card-footer">
        <button type="cancel" class="btn btn-default float-left" id="imap-cancel-btn">Cancel</button>
        <button type="submit" class="btn btn-info float-right" id="imap-submit-btn">${button}</button>
      </div>
    </form>
  </div></div></div>`
  )
 if(record){ 
    $("#imap-security").val(record.imap_security)
    $("#imap-report-schedule").val(record.imap_report_schedule)
}

$('#imap-server-address').on('change', (e)=>{ $.fn.isFieldValid(e.target,'imap-submit-btn', ['imap-server-address','imap-username','imap-password','imap-confirm-password','imap-port'])}) 
$('#imap-username').on('change', (e)=>{ $.fn.isFieldValid(e.target,'imap-submit-btn', ['imap-server-address','imap-username','imap-password','imap-confirm-password','imap-port'])}) 
$('#imap-password').on('change', (e)=>{ $.fn.isFieldValid(e.target,'imap-submit-btn', ['imap-server-address','imap-username','imap-password','imap-confirm-password','imap-port'])}) 
$('#imap-confirm-password').on('change', (e)=>{ $.fn.isFieldValid(e.target,'imap-submit-btn', ['imap-server-address','imap-username','imap-password','imap-confirm-password','imap-port'])}) 
$('#imap-port').on('change', (e)=>{ $.fn.isFieldValid(e.target,'imap-submit-btn', ['imap-server-address','imap-username','imap-password','imap-confirm-password','imap-port'])})

$("#imap-password,#imap-confirm-password").on('change', (e)=>{

  let password        = $('#imap-password').val()
  let confirmPassword = $('#imap-confirm-password').val() 

  if (password===confirmPassword){
      let classList =  $('#imap-confirm-password').attr('class')
      if (classList.indexOf('is-invalid')> -1){
        $('#imap-confirm-password').removeClass('is-invalid')
      }
      classList =  $('#imap-password').attr('class')
      if (classList.indexOf('is-invalid')> -1){
        $('#imap-password').removeClass('is-invalid')
      }

  }else{

    let classList =  $('#imap-confirm-password').attr('class')
    if (classList.indexOf('is-invalid')< 0){
       $('#imap-confirm-password').addClass('is-invalid')
    }
    classList =  $('#imap-password').attr('class')
    if (classList.indexOf('is-invalid')<0){
       $('#imap-password').addClass('is-invalid')
    }

  }

})


$('#imap-cancel-btn').on('click', (e)=>
  { 
    e.preventDefault();
    $.fn.showMailboxes(e)
  }
)

$('#imap-submit-btn').on('click', (e)=>{
    e.preventDefault();

    let address         = $('#imap-server-address').val()
    let username        = $('#imap-username').val()
    let password        = $('#imap-password').val()
    let confirmPassword = $('#imap-confirm-password').val() 
    let security        = $('#imap-security').val() 
    let reportSchedule  = $('#imap-report-schedule').val() 
    let port            = $('#imap-port').val() 
    
    if(address.length >0 && username.length > 0 && password.length > 0 && password===confirmPassword && port.length){
      
      e.preventDefault();

      let classList =  $('#imap-confirm-password').attr('class')
      if (classList.indexOf('is-invalid')> -1){
         $('#imap-confirm-password').removeClass('is-invalid')
      }
      classList =  $('#imap-password').attr('class')
      if (classList.indexOf('is-invalid')> -1){
         $('#imap-password').removeClass('is-invalid')
      }

      const formData = new FormData();
      
      formData.append("mode", titlePrefix.toLowerCase());
      if(titlePrefix.toLowerCase()=="edit"){
        formData.append('account_id', record.account_id)
      }
      formData.append("imap_server_address", address);
      formData.append("imap_username", username ); 
      formData.append("imap_password", password);
      formData.append("imap_security", security);  
      formData.append("imap_report_schedule", reportSchedule);  
      formData.append("imap_port", port);  
      
      $.ajax({
        url: "/api/add/imap",
        type: "POST",
        data: formData,
        processData: false,
        processData: false,
        contentType: false,
        crossDomain: true,
        success:  (result)=> {
            new Promise( (resolve)=>{
             resolve( $.fn.resetModal())
            }).then(()=>{
              let resultClass = result.message.toLowerCase().indexOf('success') >-1?'success':'danger'
              $.fn.showAlert(result.message,resultClass, '$.fn.showMailboxes()') 
            })
           // 
        },
        error: (e)=>{

          new Promise( (resolve)=>{
            resolve( $.fn.resetModal())
           }).then(()=>{
            
             $.fn.showAlert('IMAP Account Addition Failed','danger','$.fn.showMailboxes()') 
           })

        }
    })

    }else if(password!==confirmPassword){
      $.fn.showAlert('Passwords do not match.','danger');
      let classList =  $('#imap-confirm-password').attr('class')
      if (classList.indexOf('is-invalid')< 0){
         $('#imap-confirm-password').addClass('is-invalid')
      }
      classList =  $('#imap-password').attr('class')
      if (classList.indexOf('is-invalid')<0){
         $('#imap-password').addClass('is-invalid')
      }
         
    }else{
 
      $.fn.isFieldValid('#imap-server-address', 'imap-submit-btn', ['imap-server-address','imap-username','imap-password','imap-confirm-password','imap-port']) 
      $.fn.isFieldValid('#imap-username', 'imap-submit-btn', ['imap-server-address','imap-username','imap-password','imap-confirm-password','imap-port']) 
      $.fn.isFieldValid('#imap-password', 'imap-submit-btn', ['imap-server-address','imap-username','imap-password','imap-confirm-password','imap-port']) 
      $.fn.isFieldValid('#imap-confirm-password', 'imap-submit-btn', ['imap-server-address','imap-username','imap-password','imap-confirm-password','imap-port']) 
      $.fn.isFieldValid('#imap-port', 'imap-submit-btn', ['imap-server-address','imap-username','imap-password','imap-confirm-password','imap-port']) 
    }


})
}
)
})
}

$.fn.editGmailBox = (query='none')=>{
  let recordSelect  = new Selector([{ 
    field: "table_name"
    ,value:"Schedules"
    ,operator:Selector.EQ
  },{ 
    field: "scheduleStatus"
    ,value:1
    ,operator:Selector.EQ
  }]
  )
  $.fn.getPouchConnection().find({selector: recordSelect}).then((meta)=>{
  let results =   meta['docs'];
  return results.map((result)=>{
    return `<option value="${result.schedule_id}">${result.name}</option>`
  })


}).then((schedules) =>{
  //console.log(query)
  $.ajax({
    url: "/api/data/GMailAccounts?gmailaccounts="+JSON.stringify(query),
    type: "GET",
    processData: false,
    contentType: false,
    crossDomain: true,
    success:  (results)=> {
      
      let record= results && Object.keys(results).length==1?results['gmailaccounts'][0]:null
        let titlePrefix = record?'Edit':'New'
        let button  = record?'Update':'Add'
        $('.page-title').text(titlePrefix+' Gmail Account')
        $('#contentwrapper-node').html(
          `<div class="container-fluid"><div class="row">       
           <div class="card card-danger col-md-12 w-100">
          <div class="card-header">
            <h3 class="card-title">${titlePrefix} GMail Account</h3>
          </div>
          <form class="form-horizontal">
            <div class="card-body">
              <div class="form-group row">
                <label for="gmail-server-address" class="col-sm-2 col-form-label">GMail Server</label>
                <div class="col-sm-10">
                  <input type="text" class="form-control" name="gmail_server_address" id="gmail-server-address" value="${record?.servers?record.servers:''}" placeholder="Servers">
                </div>
              </div>
              <div class="form-group row">
              <label for="gmail-account-name" class="col-sm-2 col-form-label">Account Name</label>
              <div class="col-sm-10">
                <input type="text" class="form-control" name="gmail_account_name" id="gmail-account-name" value="${record?.account_name?record.account_name:''}"  placeholder="Account Name">
              </div>
            </div>
            <div class="form-group row">
                <label for="gmail-email-address" class="col-sm-2 col-form-label" >Email Address</label>
                <div class="col-sm-10">
                  <input type="text" class="form-control" name="gmail_email_address"  id="gmail-email-address"  value="${record?.email_address?record.email_address:''}"  placeholder="Username">
                </div>
              </div>
              <div class="form-group row">
                <label for="gmail-api-key" class="col-sm-2 col-form-label">API Key</label>
                <div class="col-sm-10">
                  <input  type="password" class="form-control" name="gmail_api_key" id="gmail-api-key" value="${record?.api_key?record.api_key:''}"  placeholder="key">
                </div>
              </div>
              <div class="form-group row">
              <label for="gmail-report-filter" class="col-sm-2 col-form-label" >Report Filter</label>
              <div class="col-sm-10">
                <input type="text" class="form-control"  id="gmail-report-filter"  value="${record?.report_filter?record.report_filter:''}"  placeholder="Report filter string">
              </div>
            </div>
            <div class="form-group row">
             <div class="col-md-2"><label>Report Schedule</label></div>
              <div class="col-md-10">
                  <select  name="gmail_report_schedule" id="gmail-report-schedule" class="form-control select2" style="width: 100%;">
                    <option selected="selected">None</option>
                  ${schedules.join('')}
                </select>
              </div>
           </div>
           <div class="form-group row">
           <div class="col-md-2"><label for="credentials-file">File input</label></div>
           <div class="input-group col-md-10">
             <div class="custom-file">
               <input type="file" class="custom-file-input" id="credentials-file">
                 <label class="custom-file-label" for="credentials-file">Choose file</label>
             </div>
           </div>
         </div>
       </div>
            <div class="card-footer">
              <button type="cancel" class="btn btn-default float-left" id="gmail-cancel-btn">Cancel</button>
              <button type="submit" class="btn btn-info float-right" id="gmail-submit-btn">${button}</button>
            </div>
          </form>
        </div></div></div>`
        )
      
        $('#gmail-cancel-btn').on('click', (e)=>{  e.preventDefault(); $.fn.showMailboxes(e)})
        $('#gmail-submit-btn').on('click', (e)=>{
      
            e.preventDefault();
            let serverAddress = $('#gmail-server-address').val()
            let accountName   = $('#gmail-account-name').val()
            let emailAddress  = $('#gmail-email-address').val()
            let apiKey        = $('#gmail-api-key').val()
            let reportFilter  = $('#gmail-report-filter').val()
            let credFile      =  $('#credentials-file').prop('files')[0],reportFile
            let reportSchedule = $('#gmail-report-schedule').val()
            
            const formData = new FormData();
            formData.append("mode", titlePrefix.toLowerCase());
            if(titlePrefix.toLowerCase()=="edit"){
                formData.append('account_id', record.account_id)
              }
            formData.append("gmail_server_address", serverAddress);
            formData.append("gmail_account_name", accountName ); 
            formData.append("gmail_email_address", emailAddress);
            formData.append("gmail_api_key", apiKey);  
            formData.append("gmail_report_filter", reportFilter);
            formData.append("report_schedule", reportSchedule);  
            formData.append("crendentials", credFile);  

              $.ajax({
              url: "/api/add/gmail",
              type: "POST",
              data: formData,
              processData: false,
              processData: false,
              contentType: false,
              crossDomain: true,
              success:  (result)=> {
                new Promise( (resolve)=>{
                  let resultClass = result.message.toLowerCase().indexOf('success') >-1?'success':'danger'
                  resolve($.fn.showAlert(result.message,resultClass,'$.fn.showMailboxes()'))
                })
              
              },
              error: (e)=>{
                new Promise( (resolve)=>{          
                  resolve($.fn.showAlert('Schedule Creation Failed','danger','$.fn.showMailboxes()'))
                })
          
              }
            })                       
          })

    },
    error: (e)=>{
      console.log(e)

    }
})}
)

}
$.fn.showMailboxes  = (e)=>{

  $.ajax({
    url: "/api/data/IMAPAccounts+GMailAccounts?imapaccounts={}&gmailaccounts={}",
    type: "GET",
    processData: false,
    contentType: false,
    crossDomain: true,
    success:  (results)=> {

      results['imapaccounts'] = results['imapaccounts'].map((row)=>{
        
        return {...row,'Actions':`<button class="btn btn-secondary btn-md" onClick="$.fn.editMailBox({'account_id': ${row.account_id}})">Edit</button><button class="btn btn-danger btn-md" onClick="$.fn.showConfirmDialog('IMAP Account Removal', 'Are you sure that you want to delete the account with id: ${row.account_id}?', '$.fn.removeIMAPAccount(${row.account_id})' )">Delete</button>`}
  
      })

      results['gmailaccounts'] = results['gmailaccounts'].map((row)=>{
        
        return {...row, credential_file: "************", token_file:"************" ,'Actions':`<button class="btn btn-secondary btn-md" onClick="$.fn.editGmailBox({'account_id': ${row.account_id}})">Edit</button><button class="btn btn-danger btn-md" onClick="$.fn.showConfirmDialog('Gmail Account Removal', 'Are you sure that you want to delete the account with id: ${row.account_id}?', '$.fn.removeGmailAccount(${row.account_id})' )">Delete</button>`}
  
      })

      
      let  imapTable = DashboardTable({"statsTitle":"Imap Accounts","statsIcon":"fa fa-envelope", "tableData":[],"id":"imap-accounts","statsClass":"primary"})
      let  gmailTable = DashboardTable({"statsTitle":"Gmail Accounts","statsIcon":"fa fa-envelope", "tableData":[],"id":"gmail-accounts","statsClass":"danger"})
      $('#contentwrapper-node').html(`<div class="container-fluid"><div class="row">${imapTable}</div>
      <div class="row">${gmailTable}</div></div>`);
       
      let columns = [ {  
        'orderable':      false,
        'data':           null,
        'defaultContent': 'No data available'
     }]
     //console.log(results['imapaccounts'][0])
     if( results['imapaccounts'] &&  results['imapaccounts'].length >0){ 
              columns[0]['defaultContent']='';
              Object.keys(results['imapaccounts'][0]).forEach((column)=>{ let col = column.split('_').map((str)=>{ return $.fn.capitalize(str)}).join(' '); columns.push({'sTitle':col,'data':column}) })
    }else{
      results['imapaccounts'][0]=[]
       
    }
     // console.log(columns)
       $('#imap-accounts').DataTable({
        "aaData": results['imapaccounts']
        ,"columns": columns,    
          "paging": true,
          "lengthChange": true,
          "searching": true,
          "ordering": true,
          "info": false,
          "autoWidth": true,
          "responsive": true
       })

       columns = [ {  
        'orderable':      false,
        'data':           null,
        'defaultContent': 'No data available'
     }]
     if( results['gmailaccounts'] &&  results['gmailaccounts'].length >0){ 
      Object.keys(results['gmailaccounts'][0]).forEach((column)=>{ let col = column.split('_').map((str)=>{ return $.fn.capitalize(str)}).join(' '); columns.push({'sTitle':col,'data':column}) })
      columns[0]['defaultContent']='';
    }else{
      results['gmailaccounts'][0]=[] 
    }
       $('#gmail-accounts').DataTable({
        "aaData": results['gmailaccounts']
        ,"columns": columns,    
          "paging": true,
          "lengthChange": true,
          "searching": true,
          "ordering": true,
          "info": false,
          "autoWidth": true,
          "responsive": true
       })
    },
    error: (e)=>{

     

    }
});


}

$.fn.showSchedules  = ()=>{
  let recordSelect  = new Selector([{ 
    field: "table_name"
    ,value:"Schedules"
    ,operator:Selector.EQ
  }]
  )
  $('.page-title').text('Schedules')
  $.fn.getPouchConnection().find({selector: recordSelect}).then((meta)=>{
    let results =   meta['docs'];
    return results
}).then((schedules) =>{
  let tableText = DashboardTable({"statsTitle":"Schedules","statsIcon":"fa fa-envelope", "tableData":[],"id":"schedules"})
  $('#contentwrapper-node').html(`<div class="container-fluid"><div class="row">${tableText}</div></div>`)
   let columns = [ {  
    'orderable':      false,
    'data':           null,
    'defaultContent': 'No data available'

  }]

 let columnNames =[];
 let newRecords =[]
if( schedules &&  schedules.length >0){ 
  schedules= schedules.map((row)=>{

    return {...row,'Actions':`<button class="btn btn-secondary btn-md" onClick="$.fn.editSchedule({'schedule_id': ${row.schedule_id}})">Edit</button><button class="btn btn-danger btn-md" onClick="$.fn.showConfirmDialog('Schedule Removal', 'Are you sure that you want to delete the schedule with id: ${row.schedule_id}?', '$.fn.removeSchedule(${row.schedule_id})' )">Delete</button>`}
    
    })
    columns[0]['defaultContent']='';
    columns.push({'sTitle':'Schedule ID','data':'schedule_id'}) 
  Object.keys(schedules[0]).filter((column)=>column!='schedule_id').forEach((column)=>{ let col = column.split('_').map((str)=>{ return $.fn.capitalize(str)}).join(' '); columns.push({'sTitle':col,'data':column});  columnNames.push(column) })
   newRecords= schedules.map((record)=>{
    record['startTime']=Object.keys(record).indexOf('startTime')>-1 ?  new Date(record['startTime']['$date']).toString():'';
	 record['last_modified_date']=Object.keys(record).indexOf('last_modified_date')>-1 ? record['last_modified_date']:'';
      return record;
  })
}else{
    newRecords =[]
}

   $('#schedules').DataTable({
    "aaData": newRecords
    ,"columns": columns,    
      "paging": true,
      "lengthChange": true,
      "searching": true,
      "ordering": true,
      "info": false,
      "autoWidth": true,
      "responsive": true
   })

})

}

$.fn.showReportEmails = ()=>{
  let recordSelect  = new Selector([{ 
    field: "table_name"
    ,value:"ReportEmails"
    ,operator:Selector.EQ
  }]
  )
  $('.page-title').text('ReportEmails')
  $.fn.getPouchConnection().find({selector: recordSelect}).then((meta)=>{
    let results =   meta['docs'];
    return results
}).then((reportEmails) =>{
  let tableText = DashboardTable({"statsTitle":"ReportEmails","statsIcon":"fa fa-envelope", "statsClass":"success","tableData":[],"id":"reportEmails"})
  $('#contentwrapper-node').html(`<div class="container-fluid"><div class="row">${tableText}</div></div>`)
   let columns = [ {  
    'orderable':      false,
    'data':           null,
    'defaultContent': 'No Data Available'
 }]
 if(  reportEmails &&   reportEmails.length >0){ 
  columns[0]['defaultContent']='';
  columns.push({'sTitle':'Report ID','data':'report_id'}) 
    Object.keys(reportEmails[0]).filter((column)=>column!='report_id').forEach((column)=>{ let col = column.split('_').map((str)=>{ return $.fn.capitalize(str)}).join(' '); columns.push({'sTitle':col,'data':column}) })
  }else{
    reportEmails =[]
  }

   $('#reportEmails').DataTable({
    "aaData": reportEmails
    ,"columns": columns,    
      "paging": true,
      "lengthChange": true,
      "searching": true,
      "ordering": true,
      "info": false,
      "autoWidth": true,
      "responsive": true
   })

})

}

$.fn.showReportUploads  = ()=>{
  let recordSelect  = new Selector([{ 
    field: "table_name"
    ,value:"ReportUploads"
    ,operator:Selector.EQ
  }]
  )
  $('.page-title').text('ReportUploads')
  $.fn.getPouchConnection().find({selector: recordSelect}).then((meta)=>{
    let results =   meta['docs'];
    return results
}).then((reportUploads) =>{
  let tableText = DashboardTable({"statsTitle":"ReportUploads","statsIcon":"fa fa-envelope", "statsClass":"primary","tableData":[],"id":"reportUploads"})
  $('#contentwrapper-node').html(`<div class="container-fluid"><div class="row">${tableText}</div></div>`)
   let columns = [ {  
    'orderable':      false,
    'data':           null,
    'defaultContent': 'No Data Available'
 }]
 if( reportUploads &&   reportUploads.length >0){ 
    columns[0]['defaultContent']='';
    columns.push({'sTitle':'Report ID','data':'report_id'}) 
    Object.keys(reportUploads[0]).filter((column)=>column!='report_id').forEach((column)=>{ let col = column.split('_').map((str)=>{ return $.fn.capitalize(str)}).join(' '); columns.push({'sTitle':col,'data':column}) })
}else{
    reportUploads =[]
}
   $('#reportUploads').DataTable({
    "aaData": reportUploads
    ,"columns": columns,    
      "paging": true,
      "lengthChange": true,
      "searching": true,
      "ordering": true,
      "info": false,
      "autoWidth": true,
      "responsive": true
   })

})


}

$.fn.showReportRecords  = ()=>{
  let recordSelect  = new Selector([{ 
    field: "table_name"
    ,value:"ReportRecords"
    ,operator:Selector.EQ
  }]
  )
  $('.page-title').text('ReportRecords')
  $.fn.getPouchConnection().find({selector: recordSelect}).then((meta)=>{
    let results =   meta['docs'];
    return results
}).then((reportRecords) =>{
  let tableText = DashboardTable({"statsTitle":"ReportRecords","statsIcon":"fa fa-envelope", "statsClass":"info","tableData":[],"id":"reportRecords"})
  $('#contentwrapper-node').html(`<div class="container-fluid"><div class="row">${tableText}</div></div>`)
   let columns = [ {  
    'orderable':      false,
    'data':           null,
    'defaultContent': 'No Data Available'
  }]
  let newRecords= []
  if(  reportRecords &&   reportRecords.length >0){ 
 
    let columnNames =[];
    columns.push({'sTitle':'Report Record ID','data':'report_record_id'})
    Object.keys(reportRecords[0]).filter((column)=>column!='report_record_id').forEach((column)=>{ let col = column.split('_').map((str)=>{ return $.fn.capitalize(str)}).join(' '); columns.push({'sTitle':col,'data':column}); columnNames.push(column)  })
    columns[0]['defaultContent']='';
     newRecords= reportRecords.map((record)=>{
      let rowColumns = 	 Object.keys(record)
      let missingColumns = 	 columnNames.filter(x => !rowColumns.includes(x));
      missingColumns.forEach((column)=>{
        record[column]='';
      })
      return record;
    })
  }else{
    newRecords =[]
  }

   $('#reportRecords').DataTable({
    "aaData": newRecords
    ,"columns": columns,    
      "paging": true,
      "lengthChange": true,
      "searching": true,
      "ordering": true,
      "info": false,
      "autoWidth": true,
      "responsive": true,
      "buttons": ["copy", "csv", "excel", "pdf", "print"] 
      }).buttons().container().appendTo('#reportRecords-table_wrapper .col-md-6:eq(0)');

})



}

$.fn.showReportMetadata  = ()=>{
  let recordSelect  = new Selector([{ 
    field: "table_name"
    ,value:"ReportMetadata"
    ,operator:Selector.EQ
  }]
  )
  $('.page-title').text('ReportMetadata')
  $.fn.getPouchConnection().find({selector: recordSelect}).then((meta)=>{
    let results =   meta['docs'];
    return results
}).then((reportMetadata) =>{
  let tableText = DashboardTable({"statsTitle":"ReportMetadata","statsIcon":"fa fa-envelope", "statsClass":"dark","tableData":[],"id":"reportMetadata"})
  $('#contentwrapper-node').html(`<div class="container-fluid"><div class="row">${tableText}</div></div>`)
   let columns = [ {  
    'orderable':      false,
    'data':           null,
    'defaultContent': 'No Data Available'
  }]
  let newRecords= []
  
  if(  reportMetadata &&   reportMetadata.length >0){ 
      let columnNames =[];
      columns.push({'sTitle':'Report ID','data':'report_id'}) 
      Object.keys(reportMetadata[0]).filter((column)=>column!='report_id').forEach((column)=>{ let col = column.split('_').map((str)=>{ return $.fn.capitalize(str)}).join(' '); columns.push({'sTitle':col,'data':column});columnNames.push(column)})
       columns[0]['defaultContent']='';
       newRecords= reportMetadata.map((record)=>{
        record['report_metadata_errors']= Object.keys(record).indexOf('report_metadata_errors')>-1?JSON.stringify(record['report_metadata_errors']):'';
        let rowColumns = 	 Object.keys(record)
        let missingColumns = 	 columnNames.filter(x => !rowColumns.includes(x));
        missingColumns.forEach((column)=>{
          record[column]='';
        })
        return record;
      })
    }else{
      newRecords =[]
  }
   $('#reportMetadata').DataTable({
    "aaData": newRecords
    ,"columns": columns,    
      "paging": true,
      "lengthChange": true,
      "searching": true,
      "ordering": true,
      "info": false,
      "autoWidth": true,
      "responsive": true,
      "buttons": ["copy", "csv", "excel", "pdf", "print"] 
      }).buttons().container().appendTo('#reportMetadata-table_wrapper .col-md-6:eq(0)');

})

}

$.fn.showJobs  = ()=>{
  let recordSelect  = new Selector([{ 
    field: "table_name"
    ,value:"Jobs"
    ,operator:Selector.EQ
  }]
  )
  $('.page-title').text('Jobs')
  $.fn.getPouchConnection().find({selector: recordSelect}).then((meta)=>{
    let results =   meta['docs'];
    return results
}).then((jobs) =>{
  let tableText = DashboardTable({"statsTitle":"Jobs","statsIcon":"fa fa-envelope", "statsClass":"danger","tableData":[],"id":"jobs"})
  $('#contentwrapper-node').html(`<div class="container-fluid"><div class="row">${tableText}</div></div>`)
   let columns = [ {  
    'orderable':      false,
    'data':           null,
    'defaultContent': 'No Data Available'
  }]
  let newRecords= []
  if(  jobs &&   jobs.length >0){ 

      let columnNames =[];
      columns.push({'sTitle':'Job ID','data':'job_id'}) 
      Object.keys(jobs[0]).filter((column)=>column!='job_id').forEach((column)=>{ let col = column.split('_').map((str)=>{ return $.fn.capitalize(str)}).join(' '); columns.push({'sTitle':col,'data':column}); columnNames.push(column)  })
      columns[0]['defaultContent']='';
      newRecords= jobs.map((record)=>{
        
      record['startTime']=Object.keys(record).indexOf('startTime')>-1 ?  new Date(record['startTime']['$date']).toString():'';
      record['endTime']=Object.keys(record).indexOf('endTime')>-1?  new Date(record['endTime']['$date']).toString():'';
      record['info']= Object.keys(record).indexOf('info')>-1?JSON.stringify(record['info']):'';
      record['errors']=Object.keys(record).indexOf('errors')>-1?JSON.stringify(record['errors']):'';
      let rowColumns = 	 Object.keys(record)
      let missingColumns = 	 columnNames.filter(x => !rowColumns.includes(x));
      missingColumns.forEach((column)=>{
        record[column]='';
      })
      return record;
      })
  }else{
    newRecords =[]
  }
   $('#jobs').DataTable({
    "aaData": newRecords
    ,"columns": columns,    
      "paging": true,
      "lengthChange": true,
      "searching": true,
      "ordering": true,
      "info": false,
      "autoWidth": true,
      "responsive": true
   })

})

}

$.fn.showDmarcRecords  = ()=>{
  let recordSelect  = new Selector([{ 
    field: "table_name"
    ,value:"DmarcRecords"
    ,operator:Selector.EQ
  }]
  )
  $('.page-title').text('DMARC Records')
  $.fn.getPouchConnection().find({selector: recordSelect}).then((meta)=>{
    let results =   meta['docs'];
    return results
}).then((dmarcRecords) =>{
  let tableText = DashboardTable({"statsTitle":"DMARC Records","statsIcon":"fa fa-history", "statsClass":"dark","tableData":[],"id":"dmarcRecords"})
  $('#contentwrapper-node').html(`<div class="container-fluid"><div class="row">${tableText}</div></div>`)
   let columns = [ {  
    'orderable':      false,
    'data':           null,
    'defaultContent': 'No data available'

 }]
 let columnNames =[];
 let newRecords =[]
if( dmarcRecords &&  dmarcRecords.length >0){ 

    columns[0]['defaultContent']='';
    columns.push({'sTitle':'Record ID','data':'record_id'}) 
  Object.keys(dmarcRecords[0]).filter((column)=>column!='record_id').forEach((column)=>{ let col = column.split('_').map((str)=>{ return $.fn.capitalize(str)}).join(' '); columns.push({'sTitle':col,'data':column});  columnNames.push(column) })
   newRecords= dmarcRecords.map((record)=>{
    record['startTime']=Object.keys(record).indexOf('startTime')>-1 ?  new Date(record['startTime']['$date']).toString():'';
  
      return record;
  })
}else{
    newRecords =[]
}

   $('#dmarcRecords').DataTable({
    "aaData": newRecords
    ,"columns": columns,    
      "paging": true,
      "lengthChange": true,
      "searching": true,
      "ordering": true,
      "info": false,
      "autoWidth": true,
      "responsive": true
   })

})

}
$.fn.getTotalDays = (month)=>{

  let days        = 31
  let DayMonths = [3,5,8,10]
  let febIndex    =  1

  if ((new Date()).getFullYear() %4==0 && month==1){
    days = 29
  }else if(month==1){
    days = 28

  }else if(DayMonths.indexOf(month) >-1){
    days = 30
  }
   return days
}

$.fn.getRepeatString = (repeat)=>{

  let repeatVal    = repeat?parseInt(repeat):0;
  let repeatString = "No";
  
  if  (repeatVal == (3600 *24 *30*12)){
  
       repeatVal = 'yearly';
   
  }else if(repeatVal == 3600 *24 *30*3){
  
    repeatString = 'quarterly';
  
  }else if(repeatVal == 3600 *24 *30){
  
    repeatString = 'monthly';
    
  }else if(repeatVal == 3600 *24 *7*2){
    repeatString = 'bi-weekly';
  }else if(repeatVal == 3600 *24 *7){
    repeatString = 'weekly'
  }else if(repeatVal == 3600 *24){
    repeatString = 'daily';
  }else if(repeatVal == 3600){
    repeatString = 'hourly';
  }else{
       repeatString="No";
  }

   return repeatString

}

$.fn.isValidDate = (element,submitBttn, siblings)=>{
 
    let startTime = $(element).val();
   // console.log(startTime)
    let startDate = startTime.length>0?  new Date(startTime):null;

    if(startDate){

      //console.log(new Date().getTime()  - startDate.getTime())
    }
    
 
    if(!startTime  ||  ( startDate && (new Date().getTime()  - startDate.getTime()) ) > 0){
   
      $(element).addClass('is-invalid')
    }else{
 
      let classList =  $(element).attr('class')
      if (classList.indexOf('is-invalid')> -1){
         $(element).removeClass('is-invalid')
      }
      for (let sibling of siblings){
        sibling = '#'+sibling;
        $.fn.isFieldValid(sibling, submitBttn, siblings) 

      }

 
    }
 



}

$.fn.editSchedule = (query)=>{
  let selector  = [{ 
    field: "table_name"
    ,value:"Schedules"
    ,operator:Selector.EQ
  }]
  //console.log(`query: ${JSON.stringify(query)}`)
    if(query && Object.keys(query).length > 0){ 
      for (let key of Object.keys(query)){
        selector.push(
          { 
            field: key
            ,value:query[key]
            ,operator:Selector.EQ
          }
        )
      }

  }else{
    selector.push(
      { 
        field: '_id'
        ,value:'-1'
        ,operator:Selector.EQ
      }
    )

  }
  
  
  let recordSelect  = new Selector( selector)
  $.fn.getPouchConnection().find({selector: recordSelect}).then((meta)=>{
      let results =   meta['docs'];
      return   results
  }).then((data) =>{

    let titlePrefix         = data && data.length>0? 'Edit'  :'New';
    let button              = data && data.length>0? 'Update':'Create';
    let record              = data[0]?data[0]: null;
  
    let scheduleName        = record && record.name? record.name: '';
    let scheduleDescription = record && record.description? record.description: '';
    let startTime           = record && record.startTime?new Date(record.startTime['$date']).toString():''
    let repeat              = record && record.repeat? $.fn.getRepeatString(record.repeat) :'No';

    $('.page-title').text(titlePrefix+' Schedule')
    $('#contentwrapper-node').html(
      `<div class="container-fluid"><div class="row">       
      <div class="card card-primary col-md-12 w-100">
      <div class="card-header">
        <h3 class="card-title">${titlePrefix} Schedule</h3>
      </div>
      <form class="form-horizontal">
        <div class="card-body">
          <div class="form-group row">
            <label for="imap-server-address" class="col-sm-2 col-form-label">Name</label>
            <div class="col-sm-10">
              <input type="text" class="form-control" name="schedule_name" id="schedule-name" placeholder="Name" value="${scheduleName}">
            </div>
          </div>
          <div class="form-group row">
          <label for="schedule-description" class="col-sm-2 col-form-label">Description</label>
          <div class="col-sm-10">
            <input type="text" name="schedule_description" id="schedule-description" class="form-control"  value="${scheduleDescription}" placeholder="Description">
          </div>
        </div>
          <div class="form-group row">
          <div class="col-md-2">  <label for="start-time">Start Time</label></div>
          <div class="col-md-10">   <div class="input-group date" data-target-input="nearest">
                  <input type="text"  name="start_time" id="start-time"  class="form-control datetimepicker-input" data-target="#start-time" value="${startTime}"/>
                  <div class="input-group-append" data-target="#start-time" data-toggle="datetimepicker">
                      <div class="input-group-text"><i class="fa fa-calendar"></i></div>
                  </div>
                  </div>
              </div>
          </div>
        <div class="form-group row">
          <div class="col-md-2"><label>Repeat</label></div>
          <div class="col-md-10">
            <select  name="schedule_repeat" id="schedule-repeat" class="form-control select2" style="width: 100%;">
              <option selected="selected" value="none">No</option>
              <option value="hourly" >Hourly</option>
              <option value="daily" >Daily</option>
              <option value="weekly" >Weekly</option>
              <option value="bi-weekly" >Bi-weekly</option>
              <option value="monthly" >Monthly</option>
            <option value="quarterly" >Quarterly</option>
            <option value="twice-a-year" >Twice-a-year</option>
            <option value="yearly" >Yearly</option>
            <option value="custom" >Custom</option>
          </select>
        </div>
        </div>
        <div class="form-group row custom d-none">
        <div class="col-md-2">
            <label> Custom</label>
        </div>
          <div class="col-2"><label for="schedule-months">Months</label>
                    <select  name="schedule_months" id="schedule-months" class="form-control select2" style="width: 100%;">
                      <option selected="selected">0</option>
                    </select>
              </div>
              <div class="col-2"><label for="schedule-weeks">Weeks</label>
                    <select  name="schedule_weeks" id="schedule-weeks" class="form-control select2" style="width: 100%;">
                      <option selected="selected">0</option>
                    </select>
              </div>
              <div class="col-2"><label for="schedule-days">Days</label>
                    <select  name="schedule_days" id="schedule-days" class="form-control select2" style="width: 100%;">
                      <option selected="selected">0</option>
                    </select>
              </div>
          </div>
          <div class="form-group row custom d-none">
            <div class="col-md-2">
            </div>
            <div class="col-2"><label for="schedule-hours">Hours</label>
                    <select  name="schedule_hours" id="schedule-hours" class="form-control select2" style="width: 100%;">
                      <option selected="selected">0</option>
                    </select>
              </div>
                <div class="col-2"><label for="schedule-minutes">Minutes</label>
                      <select  name="schedule_minutes" id="schedule-minutes" class="form-control select2" style="width: 100%;">
                        <option selected="selected">0</option>
                      </select>
                </div>
                <div class="col-2"><label for="schedule-minutes">Seconds</label>
                      <select  name="schedule_seconds" id="schedule-seconds" class="form-control select2" style="width: 100%;">
                      <option selected="selected">0</option>
                      </select>
                </div>
          </div>
    <div class="form-group row">
    <div class="col-md-2"><label>Status</label></div>
    <div class="col-md-10"><select  name="schedule_status" id="schedule-status" class="form-control select2" style="width: 100%;">
    <option selected="selected" value="active">Active</option>
    <option value="disabled" >Disabled</option>
  </select>
  </div>
        </div>
        <div class="card-footer">
          <button type="cancel" class="btn btn-default float-left" id="schedule-cancel-btn">Cancel</button>
          <button type="submit" class="btn btn-info float-right" id="schedule-submit-btn">${button}</button>
        </div>
      </form>
    </div></div></div>`

    )
    if(record){ 
    $('#start-time').val(startTime)
    $('#schedule-repeat').val(repeat)
    $('#schedule-months').val(record.moths)
    $('#schedule-weeks').val(record.weeks)
    $('#schedule-days').val(record.days)
    $('#schedule-hours').val(record.hours)
    $('#schedule-minutes').val(record.minutes)
    $('#schedule-seronds').val(record.secods)
  }

    $('#start-time').datetimepicker({ icons: { time: 'far fa-clock' } });
    $('#schedule-months').find('option').remove().end()
    for (let i=0; i<12; i++){
        $('#schedule-months').append(`<option value="${i}">${i}</option>`);
    }
    $('#schedule-weeks').find('option').remove().end()
    for (let i=0; i<4; i++){
      $('#schedule-weeks').append(`<option value="${i}">${i}</option>`);
    }
    $('#schedule-months').on('change', (e)=>{
      $('#schedule-days').find('option').remove().end()
        let  days = $.fn.getTotalDays(e.target.value)

      $('#schedule-days').find('option').remove().end()
      for (let i=0; i<days; i++){
        $('#schedule-days').append(`<option value="${i}">${i}</option>`);
      }
	
});

let  days = $.fn.getTotalDays($('#schedule-months').val())
$('#schedule-days').find('option').remove().end()
	for (let i=0; i<days; i++){
		$('#schedule-days').append(`<option value="${i}">${i}</option>`);
	}

$('#schedule-weeks').change((e)=>{
    $('#schedule-days').find('option').remove().end()
    let month = $('#schedule-months').val()
    let  days = $.fn.getTotalDays(month)

    let daysLeft = days - parseInt(e.target.value)*7
      for (let i=0; i<daysLeft; i++){
        $('#schedule-days').append(`<option value="${i}">${i}</option>`);
      }


})
   let hours = 24
   $('#schedule-hours').find('option').remove().end()
   	for (let i=0; i<hours; i++){
		$('#schedule-hours').append(`<option value="${i}">${i}</option>`);
	 }

	let count = 60
	 $(this).find('option').remove().end()
	 	for (let i=0; i<count; i++){
		$("#schedule-minutes,#schedule-seconds").append(`<option value="${i}">${i}</option>`);
	}

  $("#schedule-repeat").on('change',(e)=>{
      let value =  e.target.value;
      if (value === 'custom'){
         $('.custom').removeClass('d-none')
      }else{
        let classList  =$('.custom').attr("class")
        if (classList.indexOf('d-none')<0){ 
          $('.custom').addClass('d-none')
        }
        
      }

  })

  $('#schedule-name').on('change', (e)=>{ $.fn.isFieldValid(e.target,'schedule-submit-btn', ['schedule-name','schedule-description'])}) 
$('#schedule-description').on('change', (e)=>{ $.fn.isFieldValid(e.target,'schedule-submit-btn', ['schedule-name','schedule-description'])}) 

$('#start-time').on( 'change', (e)=>{
 // console.log('Start time changed')
  $.fn.isValidDate('#start-time','schedule-submit-btn', ['schedule-name','schedule-description'] );
})

$('#schedule-cancel-btn').on('click', (e)=>{  e.preventDefault();$.fn.showSchedules(e)})
$('#schedule-submit-btn').on('click', (e)=>{

    let scheduleName            = $('#schedule-name').val()
    let scheduleDescription     = $('#schedule-description').val()
    let startTime               = $('#start-time').val() 
    let status          		    = $('#schedule-status').val() 
    let scheduleRepeat			    = $('#schedule-repeat').val() 
	
    let months                    = 0
    let weeks                    = 0
    let days                     = 0
    let hours                    = 0
    let minutes                  = 0
    let seconds                  = 0
	
	if (scheduleRepeat ==='custom'){
	
	   months = $('#schedule-months').val();
	   weeks = $('#schedule-weeks').val();
	   days = $('#schedule-days').val();
	   hours = $('#schedule-hours').val();
	   minutes = $('#schedule-minutes').val();
	   seconds = $('#schedule-seconds').val();
	}
    e.preventDefault();
    if( startTime.length > 0 &&   (Date.parse(startTime) - (new Date())) <0  ){
     $.fn.showAlert('Start time cannot be in the past unless you are The Flash','danger')
    }else if(scheduleName.length >0 && scheduleDescription.length > 0 && startTime.length > 0){
      

        const formData = new FormData();
        formData.append("mode", titlePrefix.toLowerCase());
        if(titlePrefix.toLowerCase()=="edit"){
          formData.append('schedule_id', record.schedule_id)
        }
        formData.append("schedule_name", scheduleName);
        formData.append("schedule_description", scheduleDescription ); 
        formData.append("startTime", startTime);
        formData.append("scheduleStatus", status);  
        formData.append("schedule_repeat", scheduleRepeat);  
        formData.append("months", months);  
        formData.append("weeks", weeks);  
        formData.append("days", days);  
        formData.append("hours", hours);
        formData.append("minutes", minutes); 
        formData.append("seconds", seconds); 		
          
          $.ajax({
          url: "/api/add/schedule",
          type: "POST",
          data: formData,
          processData: false,
          processData: false,
          contentType: false,
          crossDomain: true,
          success:  (result)=> {
            new Promise( (resolve)=>{
              let resultClass = result.message.toLowerCase().indexOf('success') >-1?'success':'danger'
               $.fn.showAlert(result.message,resultClass,'$.fn.showSchedules()') 
            })
          
          },
          error: (e)=>{
            new Promise( (resolve)=>{          
            $.fn.showAlert('Schedule Creation Failed','danger','$.fn.showSchedules()') 
            })

          }
        })

        }else{	 
          $.fn.isFieldValid('#schedule-name', 'schedule-submit-btn', ['schedule-name','schedule-description']) 
          $.fn.isFieldValid('#schedule-description', 'schedule-submit-btn', ['schedule-name','schedule-description']) 
          $.fn.isValidDate('#start-time','schedule-submit-btn', ['schedule-name','schedule-description'] );
       }

  })
})

}

if (syncWorker) {
  syncWorker.postMessage(['start', window.config]);
}else{
  startSync();
}

