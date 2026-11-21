export type Airport={iata:string;name:string;city:string;country:string;countryCode:string;lat?:number;lon?:number};
export type Offer={number:string;airline:string;origin:string;destination:string;departure:string;arrival:string;duration:string;stops:number;fare:number;currency:string;baggage:number;source:'AMADEUS'|'DEMO_DYNAMIC'};
const raw=`DEL|Indira Gandhi International|Delhi|India|IN|28.556|77.100
BOM|Chhatrapati Shivaji Maharaj International|Mumbai|India|IN|19.089|72.868
BLR|Kempegowda International|Bengaluru|India|IN|13.199|77.706
HYD|Rajiv Gandhi International|Hyderabad|India|IN|17.240|78.429
MAA|Chennai International|Chennai|India|IN|12.994|80.171
CCU|Netaji Subhas Chandra Bose International|Kolkata|India|IN|22.654|88.447
COK|Cochin International|Kochi|India|IN|10.152|76.401
AMD|Sardar Vallabhbhai Patel International|Ahmedabad|India|IN|23.073|72.635
GOI|Dabolim Airport|Goa|India|IN|15.381|73.831
GOX|Manohar International|Goa|India|IN|15.744|73.860
PNQ|Pune International|Pune|India|IN|18.582|73.920
JAI|Jaipur International|Jaipur|India|IN|26.824|75.812
LKO|Chaudhary Charan Singh International|Lucknow|India|IN|26.761|80.889
GAU|Lokpriya Gopinath Bordoloi International|Guwahati|India|IN|26.106|91.586
TRV|Thiruvananthapuram International|Thiruvananthapuram|India|IN|8.482|76.920
IXC|Chandigarh International|Chandigarh|India|IN|30.674|76.789
BBI|Biju Patnaik International|Bhubaneswar|India|IN|20.244|85.818
PAT|Jay Prakash Narayan|Patna|India|IN|25.591|85.088
SXR|Sheikh ul-Alam International|Srinagar|India|IN|33.987|74.774
IXB|Bagdogra International|Siliguri|India|IN|26.681|88.328
VNS|Lal Bahadur Shastri International|Varanasi|India|IN|25.452|82.859
ATQ|Sri Guru Ram Dass Jee International|Amritsar|India|IN|31.710|74.797
IDR|Devi Ahilya Bai Holkar|Indore|India|IN|22.722|75.801
NAG|Dr Babasaheb Ambedkar International|Nagpur|India|IN|21.092|79.047
IXR|Birsa Munda|Ranchi|India|IN|23.314|85.322
VTZ|Visakhapatnam International|Visakhapatnam|India|IN|17.721|83.225
CJB|Coimbatore International|Coimbatore|India|IN|11.030|77.043
IXM|Madurai International|Madurai|India|IN|9.834|78.093
IXE|Mangaluru International|Mangaluru|India|IN|12.961|74.890
TRZ|Tiruchirappalli International|Tiruchirappalli|India|IN|10.765|78.709
UDR|Maharana Pratap|Udaipur|India|IN|24.617|73.896
JDH|Jodhpur Airport|Jodhpur|India|IN|26.251|73.048
DED|Dehradun Jolly Grant|Dehradun|India|IN|30.190|78.180
IXJ|Jammu Airport|Jammu|India|IN|32.689|74.838
IXZ|Veer Savarkar International|Port Blair|India|IN|11.641|92.730
LEH|Kushok Bakula Rimpochee|Leh|India|IN|34.136|77.547
STV|Surat International|Surat|India|IN|21.115|72.743
BDQ|Vadodara Airport|Vadodara|India|IN|22.336|73.226
RPR|Swami Vivekananda|Raipur|India|IN|21.180|81.739
IXA|Maharaja Bir Bikram|Agartala|India|IN|23.887|91.240
IXS|Silchar Airport|Silchar|India|IN|24.913|92.979
DIB|Dibrugarh Airport|Dibrugarh|India|IN|27.484|95.016
IMF|Imphal International|Imphal|India|IN|24.760|93.897
SHL|Shillong Airport|Shillong|India|IN|25.704|91.978
DMU|Dimapur Airport|Dimapur|India|IN|25.883|93.771
AJL|Lengpui Airport|Aizawl|India|IN|23.840|92.619
GAY|Gaya Airport|Gaya|India|IN|24.744|84.951
IXD|Prayagraj Airport|Prayagraj|India|IN|25.440|81.734
KNU|Kanpur Airport|Kanpur|India|IN|26.404|80.410
GWL|Rajmata Vijaya Raje Scindia|Gwalior|India|IN|26.293|78.228
BHO|Raja Bhoj|Bhopal|India|IN|23.288|77.337
JLR|Jabalpur Airport|Jabalpur|India|IN|23.178|80.052
RAJ|Rajkot International|Rajkot|India|IN|22.378|71.039
BHJ|Bhuj Airport|Bhuj|India|IN|23.288|69.670
JGA|Jamnagar Airport|Jamnagar|India|IN|22.466|70.012
PBD|Porbandar Airport|Porbandar|India|IN|21.649|69.657
HBX|Hubballi Airport|Hubballi|India|IN|15.362|75.085
MYQ|Mysuru Airport|Mysuru|India|IN|12.230|76.656
VGA|Vijayawada International|Vijayawada|India|IN|16.530|80.797
TIR|Tirupati Airport|Tirupati|India|IN|13.633|79.543
RJA|Rajahmundry Airport|Rajahmundry|India|IN|17.110|81.818
CNN|Kannur International|Kannur|India|IN|11.918|75.547
CCJ|Calicut International|Kozhikode|India|IN|11.137|75.955
AGX|Agatti Airport|Lakshadweep|India|IN|10.823|72.176
DXB|Dubai International|Dubai|United Arab Emirates|AE|25.253|55.365
AUH|Zayed International|Abu Dhabi|United Arab Emirates|AE|24.433|54.651
DOH|Hamad International|Doha|Qatar|QA|25.273|51.608
SIN|Singapore Changi|Singapore|Singapore|SG|1.364|103.991
BKK|Suvarnabhumi|Bangkok|Thailand|TH|13.690|100.750
KUL|Kuala Lumpur International|Kuala Lumpur|Malaysia|MY|2.745|101.710
LHR|Heathrow|London|United Kingdom|GB|51.470|-0.454
LGW|Gatwick|London|United Kingdom|GB|51.153|-0.190
CDG|Charles de Gaulle|Paris|France|FR|49.010|2.548
FRA|Frankfurt Airport|Frankfurt|Germany|DE|50.038|8.562
AMS|Amsterdam Schiphol|Amsterdam|Netherlands|NL|52.310|4.768
ZRH|Zurich Airport|Zurich|Switzerland|CH|47.458|8.555
IST|Istanbul Airport|Istanbul|Türkiye|TR|41.275|28.751
JFK|John F Kennedy International|New York|United States|US|40.641|-73.778
EWR|Newark Liberty International|New York|United States|US|40.689|-74.174
LAX|Los Angeles International|Los Angeles|United States|US|33.942|-118.408
SFO|San Francisco International|San Francisco|United States|US|37.621|-122.379
ORD|O'Hare International|Chicago|United States|US|41.974|-87.907
YYZ|Toronto Pearson International|Toronto|Canada|CA|43.677|-79.630
YVR|Vancouver International|Vancouver|Canada|CA|49.196|-123.181
SYD|Sydney Kingsford Smith|Sydney|Australia|AU|-33.939|151.175
MEL|Melbourne Airport|Melbourne|Australia|AU|-37.670|144.843
NRT|Narita International|Tokyo|Japan|JP|35.772|140.392
HND|Tokyo Haneda|Tokyo|Japan|JP|35.550|139.780
ICN|Incheon International|Seoul|South Korea|KR|37.460|126.440
HKG|Hong Kong International|Hong Kong|Hong Kong|HK|22.308|113.918
PEK|Beijing Capital International|Beijing|China|CN|40.080|116.585
PVG|Shanghai Pudong International|Shanghai|China|CN|31.145|121.808
CGK|Soekarno-Hatta International|Jakarta|Indonesia|ID|-6.126|106.656
MLE|Velana International|Malé|Maldives|MV|4.192|73.529
CMB|Bandaranaike International|Colombo|Sri Lanka|LK|7.181|79.884
KTM|Tribhuvan International|Kathmandu|Nepal|NP|27.696|85.359
DAC|Hazrat Shahjalal International|Dhaka|Bangladesh|BD|23.843|90.398
JED|King Abdulaziz International|Jeddah|Saudi Arabia|SA|21.680|39.157
RUH|King Khalid International|Riyadh|Saudi Arabia|SA|24.958|46.699
CAI|Cairo International|Cairo|Egypt|EG|30.121|31.406
JNB|O.R. Tambo International|Johannesburg|South Africa|ZA|-26.136|28.241
NBO|Jomo Kenyatta International|Nairobi|Kenya|KE|-1.319|36.928`;
export const airportCatalog:Airport[]=raw.split('\n').map(x=>{const[iata,name,city,country,countryCode,lat,lon]=x.split('|');return{iata,name,city,country,countryCode,lat:+lat,lon:+lon}});
const airlineNames:Record<string,string>={AI:'Air India',UK:'Vistara','6E':'IndiGo',SG:'SpiceJet',QP:'Akasa Air',IX:'Air India Express',EK:'Emirates',EY:'Etihad Airways',QR:'Qatar Airways',SQ:'Singapore Airlines',BA:'British Airways',LH:'Lufthansa',AF:'Air France',TK:'Turkish Airlines',CX:'Cathay Pacific',TG:'Thai Airways',MH:'Malaysia Airlines',UA:'United Airlines',AA:'American Airlines'};
export class AmadeusProvider{
 private token='';private expires=0; constructor(private key=process.env.AMADEUS_API_KEY||'',private secret=process.env.AMADEUS_API_SECRET||'',private base=process.env.AMADEUS_BASE_URL||'https://test.api.amadeus.com'){}
 get configured(){return!!(this.key&&this.secret)}
 private async auth(){if(this.token&&Date.now()<this.expires)return this.token;const body=new URLSearchParams({grant_type:'client_credentials',client_id:this.key,client_secret:this.secret});const r=await fetch(this.base+'/v1/security/oauth2/token',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body});if(!r.ok)throw Error(`Amadeus authentication failed (${r.status})`);const d:any=await r.json();this.token=d.access_token;this.expires=Date.now()+(d.expires_in-60)*1000;return this.token}
 private async get(path:string){const token=await this.auth();const r=await fetch(this.base+path,{headers:{Authorization:`Bearer ${token}`}});if(!r.ok)throw Error(`Amadeus request failed (${r.status})`);return r.json() as Promise<any>}
 async airports(keyword:string):Promise<Airport[]>{const d=await this.get(`/v1/reference-data/locations?subType=AIRPORT&keyword=${encodeURIComponent(keyword)}&page[limit]=20&view=LIGHT`);return(d.data||[]).map((x:any)=>({iata:x.iataCode,name:x.name,city:x.address?.cityName||x.detailedName,country:x.address?.countryName||x.address?.countryCode,countryCode:x.address?.countryCode,lat:x.geoCode?.latitude,lon:x.geoCode?.longitude}))}
 async offers(origin:string,destination:string,date:string,adults=1,cabin='ECONOMY'):Promise<Offer[]>{const p=new URLSearchParams({originLocationCode:origin,destinationLocationCode:destination,departureDate:date,adults:String(adults),travelClass:cabin,currencyCode:'INR',max:'20'});const d=await this.get('/v2/shopping/flight-offers?'+p);const dictionaries=d.dictionaries?.carriers||{};return(d.data||[]).map((o:any)=>{const it=o.itineraries[0],segs=it.segments,first=segs[0],last=segs[segs.length-1],code=first.carrierCode;return{number:code+first.number,airline:dictionaries[code]||airlineNames[code]||code,origin:first.departure.iataCode,destination:last.arrival.iataCode,departure:first.departure.at,arrival:last.arrival.at,duration:it.duration,stops:segs.length-1,fare:Math.round(Number(o.price.grandTotal)),currency:o.price.currency||'INR',baggage:o.travelerPricings?.[0]?.fareDetailsBySegment?.[0]?.includedCheckedBags?.weight||15,source:'AMADEUS'}})} }
function hash(s:string){let h=2166136261;for(const c of s)h=Math.imul(h^c.charCodeAt(0),16777619);return h>>>0}
export function dynamicOffers(origin:string,destination:string,date:string):Offer[]{const seed=hash(origin+destination+date),international=airportCatalog.find(x=>x.iata===destination)?.countryCode!=='IN',base=international?9500+(seed%18000):2600+(seed%4200),codes=international?['AI','EK','6E','QR']:['6E','AI','QP','SG'];return codes.map((code,i)=>{const hour=6+i*4+(seed%2),mins=(seed+i*17)%60,duration=international?180+(seed%360):65+(seed%130),depart=new Date(`${date}T${String(hour).padStart(2,'0')}:${String(mins).padStart(2,'0')}:00`),arrive=new Date(depart.getTime()+duration*60000),stops=i===3&&international?1:0;return{number:`${code}${100+(seed+i*137)%899}`,airline:airlineNames[code],origin,destination,departure:depart.toISOString(),arrival:arrive.toISOString(),duration:`PT${Math.floor(duration/60)}H${duration%60}M`,stops,fare:Math.round((base+i*730+(stops?-1200:0))/10)*10,currency:'INR',baggage:international?25:15,source:'DEMO_DYNAMIC'}})}
export const amadeus=new AmadeusProvider();
