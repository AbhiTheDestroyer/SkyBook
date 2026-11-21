import type Database from'better-sqlite3';
export class GateService{constructor(private db:Database.Database){}getGate(gate:string){return this.db.prepare('SELECT g.*,n.node_key,n.name FROM navigation_gates g JOIN navigation_nodes n ON n.id=g.node_id WHERE g.gate_number=? AND g.active=1 AND n.active=1').get(gate.toUpperCase())}}
