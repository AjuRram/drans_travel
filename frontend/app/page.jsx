"use client";

import React, { useEffect, useMemo, useState } from "react";
import {
  Building2, CalendarDays, Car, Check, ChevronRight, CircleDollarSign,
  Compass, Hotel, LogOut, Menu, Plane, Plus, Search, Sparkles, Ticket,
  UserRound, UsersRound, X
} from "lucide-react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const DEMO_MODE = process.env.NEXT_PUBLIC_DEMO_MODE === "true";
const DEMO_USERS = {
  client: { id: 3, organization_id: 1, email: "client@acme.demo", full_name: "Aarav Sharma", role: "client", phone: "+91 90000 00000", job_title: "Regional Manager", preferences: { seat: "aisle", hotel: "4-star", meal: "vegetarian" }, active: true },
  agent: { id: 2, organization_id: null, email: "agent@voyageai.demo", full_name: "Travel Agent", role: "agent", phone: "", job_title: "Travel Consultant", preferences: {}, active: true },
  admin: { id: 1, organization_id: null, email: "admin@voyageai.demo", full_name: "Platform Administrator", role: "admin", phone: "", job_title: "Administrator", preferences: {}, active: true },
};

function demoRead(key, fallback) {
  try { return JSON.parse(localStorage.getItem(key)) ?? fallback; } catch { return fallback; }
}
function demoWrite(key, value) {
  localStorage.setItem(key, JSON.stringify(value));
  return value;
}
function demoApi(path, options = {}) {
  const method = options.method || "GET";
  const body = options.body ? JSON.parse(options.body) : {};
  const requests = demoRead("voyage-demo-requests", []);
  const organizations = demoRead("voyage-demo-organizations", [
    { id: 1, name: "Acme Corporation", code: "ACME", billing_email: "billing@acme.demo", active: true, created_at: new Date().toISOString() },
  ]);
  if (path === "/api/travel/requests" && method === "GET") return Promise.resolve(requests);
  if (path === "/api/travel/requests" && method === "POST") {
    const item = { ...body, id: Date.now(), reference: `TRV-DEMO-${String(requests.length + 1).padStart(3, "0")}`, client_id: 3, assigned_agent_id: null, status: "submitted", details: body.details || {}, quote_amount: null, created_at: new Date().toISOString(), updated_at: new Date().toISOString() };
    demoWrite("voyage-demo-requests", [item, ...requests]);
    return Promise.resolve(item);
  }
  if (path.startsWith("/api/travel/requests/") && method === "PATCH") {
    const id = Number(path.split("/")[4]);
    const updated = requests.map(item => item.id === id ? { ...item, ...body, updated_at: new Date().toISOString() } : item);
    demoWrite("voyage-demo-requests", updated);
    return Promise.resolve(updated.find(item => item.id === id));
  }
  if (path === "/api/profile" && method === "PATCH") return Promise.resolve(body);
  if (path === "/api/organizations" && method === "GET") return Promise.resolve(organizations);
  if (path === "/api/organizations" && method === "POST") {
    const item = { ...body, id: Date.now(), code: body.code.toUpperCase(), active: true, created_at: new Date().toISOString() };
    demoWrite("voyage-demo-organizations", [item, ...organizations]);
    return Promise.resolve(item);
  }
  if (path === "/api/users" && method === "POST") return Promise.resolve({ ...body, id: Date.now(), role: "client", active: true });
  if (path === "/api/reports/summary") return Promise.resolve({ organizations: organizations.length, clients: 1, requests: requests.length, bookings: requests.filter(r => r.status === "booked").length, invoiced_revenue: 0, requests_by_status: {}, requests_by_service: {} });
  if (path === "/api/bookings" || path === "/api/invoices") return Promise.resolve([]);
  return Promise.resolve({});
}
const SERVICES = [
  { id: "flight", label: "Flights", icon: Plane, color: "#725cff" },
  { id: "hotel", label: "Hotels", icon: Hotel, color: "#ff725e" },
  { id: "bus", label: "Buses", icon: Ticket, color: "#18a999" },
  { id: "cab", label: "Cabs", icon: Car, color: "#f2a900" },
  { id: "event", label: "Events", icon: CalendarDays, color: "#d94f90" },
];

async function api(path, options = {}, token = "") {
  if (DEMO_MODE) return demoApi(path, options);
  const headers = { ...(options.headers || {}) };
  if (!(options.body instanceof FormData)) headers["Content-Type"] = "application/json";
  if (token) headers.Authorization = `Bearer ${token}`;
  const response = await fetch(`${API}${path}`, { ...options, headers });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(payload.detail || "Something went wrong");
  return payload;
}

function Login({ onLogin }) {
  const [email, setEmail] = useState("client@acme.demo");
  const [password, setPassword] = useState("Client123!");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (event) => {
    event.preventDefault(); setBusy(true); setError("");
    try {
      let data;
      if (DEMO_MODE) {
        const role = email.startsWith("admin") ? "admin" : email.startsWith("agent") ? "agent" : "client";
        data = { access_token: `demo-${role}-token`, token_type: "bearer", user: DEMO_USERS[role] };
      } else {
        const body = new URLSearchParams({ username: email, password });
        const response = await fetch(`${API}/api/auth/login`, {
          method: "POST", headers: { "Content-Type": "application/x-www-form-urlencoded" }, body
        });
        data = await response.json();
        if (!response.ok) throw new Error(data.detail);
      }
      onLogin(data);
    } catch (err) { setError(err.message); } finally { setBusy(false); }
  };

  const demo = (role) => {
    const users = {
      client: ["client@acme.demo", "Client123!"],
      agent: ["agent@voyageai.demo", "Agent123!"],
      admin: ["admin@voyageai.demo", "Admin123!"],
    };
    setEmail(users[role][0]); setPassword(users[role][1]);
  };

  return <main className="login-page">
    <section className="login-story">
      <div className="brand"><span><Compass size={22}/></span> VoyageAI</div>
      <div className="story-copy">
        <div className="eyebrow">CORPORATE TRAVEL, REIMAGINED</div>
        <h1>Every journey.<br/><em>One intelligent desk.</em></h1>
        <p>Plan, approve, book and understand business travel from a workspace built for modern teams.</p>
        <div className="trust-row">
          <span><Check size={15}/> Policy-aware</span>
          <span><Check size={15}/> Human-supported</span>
          <span><Check size={15}/> One clear view</span>
        </div>
      </div>
      <div className="route-card">
        <div><small>NEXT JOURNEY</small><b>Coimbatore <ChevronRight/> Singapore</b></div>
        <span>14 Sep · 3 travelers</span>
      </div>
    </section>
    <section className="login-panel">
      <form onSubmit={submit} className="login-form">
        <div className="mobile-brand"><Compass/> VoyageAI</div>
        <span className="kicker">WELCOME BACK</span>
        <h2>Sign in to your workspace</h2>
        <p className="muted">Manage requests, bookings and travelers in one place.</p>
        <label>Work email<input value={email} onChange={e => setEmail(e.target.value)} type="email" required/></label>
        <label>Password<input value={password} onChange={e => setPassword(e.target.value)} type="password" required/></label>
        {error && <div className="error">{error}</div>}
        <button className="primary" disabled={busy}>{busy ? "Signing in…" : "Sign in"} <ChevronRight size={18}/></button>
        <div className="demo-box">
          <small>DEMO WORKSPACES</small>
          <div>{["client", "agent", "admin"].map(role =>
            <button type="button" key={role} onClick={() => demo(role)}>{role}</button>)}</div>
        </div>
        <p className="secure-note">Protected workspace · Demo environment</p>
      </form>
    </section>
  </main>;
}

function Stat({ label, value, detail, icon: Icon }) {
  return <article className="stat"><span><Icon size={19}/></span><div><small>{label}</small><strong>{value}</strong><p>{detail}</p></div></article>;
}

function RequestModal({ token, close, saved }) {
  const [form, setForm] = useState({
    service_type: "flight", origin: "Coimbatore", destination: "",
    start_date: "", end_date: "", travelers: 1, budget: 0, currency: "INR", notes: ""
  });
  const [error, setError] = useState("");
  const submit = async e => {
    e.preventDefault();
    try {
      await api("/api/travel/requests", { method: "POST", body: JSON.stringify(form) }, token);
      saved(); close();
    } catch (err) { setError(err.message); }
  };
  return <div className="modal-backdrop"><form className="modal" onSubmit={submit}>
    <button className="close" type="button" onClick={close}><X/></button>
    <span className="kicker">NEW JOURNEY</span><h2>Tell us where you're going</h2>
    <div className="service-picker">{SERVICES.map(({id,label,icon:Icon}) =>
      <button type="button" className={form.service_type === id ? "active" : ""} onClick={() => setForm({...form, service_type:id})} key={id}><Icon/>{label}</button>)}</div>
    <div className="form-grid">
      <label>From<input value={form.origin} onChange={e => setForm({...form, origin:e.target.value})}/></label>
      <label>Destination<input required value={form.destination} onChange={e => setForm({...form, destination:e.target.value})}/></label>
      <label>Start date<input required type="date" value={form.start_date} onChange={e => setForm({...form, start_date:e.target.value})}/></label>
      <label>End date<input required type="date" value={form.end_date} onChange={e => setForm({...form, end_date:e.target.value})}/></label>
      <label>Travelers<input min="1" type="number" value={form.travelers} onChange={e => setForm({...form, travelers:+e.target.value})}/></label>
      <label>Budget (INR)<input min="0" type="number" value={form.budget} onChange={e => setForm({...form, budget:+e.target.value})}/></label>
    </div>
    <label>Notes<textarea value={form.notes} onChange={e => setForm({...form, notes:e.target.value})} placeholder="Seat, hotel, accessibility or event requirements…"/></label>
    {error && <div className="error">{error}</div>}
    <button className="primary">Submit travel request <ChevronRight size={18}/></button>
  </form></div>;
}

function EditRequestModal({ token, request, close, saved }) {
  const [form, setForm] = useState({
    origin: request.origin, destination: request.destination,
    start_date: request.start_date, end_date: request.end_date,
    travelers: request.travelers, budget: request.budget, notes: request.notes || ""
  });
  const [error, setError] = useState("");
  const submit = async e => {
    e.preventDefault();
    try {
      await api(`/api/travel/requests/${request.id}`, {method:"PATCH", body:JSON.stringify(form)}, token);
      saved(); close();
    } catch (err) { setError(err.message); }
  };
  return <div className="modal-backdrop"><form className="modal" onSubmit={submit}>
    <button className="close" type="button" onClick={close}><X/></button>
    <span className="kicker">MODIFY REQUEST · {request.reference}</span><h2>Update journey details</h2>
    <div className="form-grid">
      <label>From<input value={form.origin} onChange={e=>setForm({...form,origin:e.target.value})}/></label>
      <label>Destination<input required value={form.destination} onChange={e=>setForm({...form,destination:e.target.value})}/></label>
      <label>Start date<input required type="date" value={form.start_date} onChange={e=>setForm({...form,start_date:e.target.value})}/></label>
      <label>End date<input required type="date" value={form.end_date} onChange={e=>setForm({...form,end_date:e.target.value})}/></label>
      <label>Travelers<input min="1" type="number" value={form.travelers} onChange={e=>setForm({...form,travelers:+e.target.value})}/></label>
      <label>Budget (INR)<input min="0" type="number" value={form.budget} onChange={e=>setForm({...form,budget:+e.target.value})}/></label>
    </div>
    <label>Notes<textarea value={form.notes} onChange={e=>setForm({...form,notes:e.target.value})}/></label>
    {error && <div className="error">{error}</div>}
    <button className="primary">Save changes <Check size={18}/></button>
  </form></div>;
}

function ProfilePanel({ token, initial }) {
  const [form, setForm] = useState({
    full_name: initial.full_name, phone: initial.phone || "", job_title: initial.job_title || "",
    passport_number: "", preferences: initial.preferences || {}
  });
  const [message, setMessage] = useState("");
  const save = async e => {
    e.preventDefault(); setMessage("");
    try { await api("/api/profile",{method:"PATCH",body:JSON.stringify(form)},token); setMessage("Profile updated successfully."); }
    catch (err) { setMessage(err.message); }
  };
  return <form className="panel profile-panel" onSubmit={save}>
    <div className="panel-title"><div><span className="kicker">TRAVELER ACCOUNT</span><h3>Profile and preferences</h3></div></div>
    <div className="profile-avatar">{initial.full_name[0]}</div>
    <div className="form-grid">
      <label>Full name<input value={form.full_name} onChange={e=>setForm({...form,full_name:e.target.value})}/></label>
      <label>Work email<input disabled value={initial.email}/></label>
      <label>Phone<input value={form.phone} onChange={e=>setForm({...form,phone:e.target.value})}/></label>
      <label>Job title<input value={form.job_title} onChange={e=>setForm({...form,job_title:e.target.value})}/></label>
      <label>Seat preference<input value={form.preferences.seat || ""} onChange={e=>setForm({...form,preferences:{...form.preferences,seat:e.target.value}})}/></label>
      <label>Meal preference<input value={form.preferences.meal || ""} onChange={e=>setForm({...form,preferences:{...form.preferences,meal:e.target.value}})}/></label>
    </div>
    {message && <div className="success-message">{message}</div>}
    <button className="primary compact">Save profile</button>
  </form>;
}

function OnboardModal({ token, organizations, close, saved }) {
  const [mode,setMode]=useState("organization");
  const [form,setForm]=useState({name:"",code:"",billing_email:"",email:"",full_name:"",password:"",organization_id:""});
  const [error,setError]=useState("");
  const submit=async e=>{
    e.preventDefault();
    try{
      if(mode==="organization") await api("/api/organizations",{method:"POST",body:JSON.stringify({name:form.name,code:form.code,billing_email:form.billing_email})},token);
      else await api("/api/users",{method:"POST",body:JSON.stringify({email:form.email,full_name:form.full_name,password:form.password,role:"client",organization_id:+form.organization_id})},token);
      saved();close();
    }catch(err){setError(err.message)}
  };
  return <div className="modal-backdrop"><form className="modal onboard" onSubmit={submit}>
    <button className="close" type="button" onClick={close}><X/></button>
    <span className="kicker">ADMIN ONBOARDING</span><h2>Add a B2B account</h2>
    <div className="mode-switch"><button type="button" className={mode==="organization"?"active":""} onClick={()=>setMode("organization")}>Organization</button><button type="button" className={mode==="client"?"active":""} onClick={()=>setMode("client")}>Client user</button></div>
    {mode==="organization"?<div className="form-grid">
      <label>Organization name<input required value={form.name} onChange={e=>setForm({...form,name:e.target.value})}/></label>
      <label>Account code<input required value={form.code} onChange={e=>setForm({...form,code:e.target.value})}/></label>
      <label>Billing email<input required type="email" value={form.billing_email} onChange={e=>setForm({...form,billing_email:e.target.value})}/></label>
    </div>:<div className="form-grid">
      <label>Full name<input required value={form.full_name} onChange={e=>setForm({...form,full_name:e.target.value})}/></label>
      <label>Work email<input required type="email" value={form.email} onChange={e=>setForm({...form,email:e.target.value})}/></label>
      <label>Temporary password<input required minLength="8" type="password" value={form.password} onChange={e=>setForm({...form,password:e.target.value})}/></label>
      <label>Organization<select required value={form.organization_id} onChange={e=>setForm({...form,organization_id:e.target.value})}><option value="">Select…</option>{organizations.map(o=><option value={o.id} key={o.id}>{o.name}</option>)}</select></label>
    </div>}
    {error&&<div className="error">{error}</div>}<button className="primary">Complete onboarding <ChevronRight size={18}/></button>
  </form></div>;
}

function Dashboard({ session, logout }) {
  const { access_token: token, user } = session;
  const [requests, setRequests] = useState([]);
  const [report, setReport] = useState({});
  const [organizations, setOrganizations] = useState([]);
  const [showRequest, setShowRequest] = useState(false);
  const [editing, setEditing] = useState(null);
  const [showOnboard, setShowOnboard] = useState(false);
  const [navOpen, setNavOpen] = useState(false);
  const [page, setPage] = useState("Overview");

  const load = async () => {
    try {
      setRequests(await api("/api/travel/requests", {}, token));
      if (user.role !== "client") {
        setReport(await api("/api/reports/summary", {}, token));
        setOrganizations(await api("/api/organizations", {}, token));
      }
    } catch (err) { console.error(err); }
  };
  useEffect(() => { load(); }, []);
  const isAdmin = user.role !== "client";
  const counts = useMemo(() => ({
    active: requests.filter(r => !["booked","cancelled"].includes(r.status)).length,
    booked: requests.filter(r => r.status === "booked").length,
  }), [requests]);

  return <div className="app-shell">
    <aside className={navOpen ? "sidebar open" : "sidebar"}>
      <div className="brand"><span><Compass size={20}/></span> VoyageAI</div>
      <button className="mobile-close" onClick={() => setNavOpen(false)}><X/></button>
      <nav>
        {[
          ["Overview", Compass], ["Travel requests", CalendarDays],
          ["Bookings", Ticket], ["Travelers", UsersRound],
          ...(isAdmin ? [["Organizations", Building2], ["Reports", CircleDollarSign]] : [["My profile", UserRound]])
        ].map(([label,Icon]) => <button key={label} className={page === label ? "active" : ""} onClick={() => {setPage(label);setNavOpen(false)}}><Icon/>{label}</button>)}
      </nav>
      <div className="sidebar-user"><div>{user.full_name[0]}</div><span><b>{user.full_name}</b><small>{user.role} workspace</small></span><button onClick={logout}><LogOut/></button></div>
    </aside>
    <main className="workspace">
      <header>
        <button className="menu" onClick={() => setNavOpen(true)}><Menu/></button>
        <div><span className="kicker">{isAdmin ? "OPERATIONS COMMAND" : "YOUR TRAVEL DESK"}</span><h1>{page}</h1></div>
        <button className="primary compact" onClick={() => setShowRequest(true)}><Plus/> New request</button>
      </header>

      {page === "Overview" && <>
        <section className="welcome">
          <div><span className="kicker">{new Date().toLocaleDateString("en-IN", {weekday:"long",day:"numeric",month:"long"})}</span>
          <h2>{isAdmin ? "The travel desk is under control." : `Good to see you, ${user.full_name.split(" ")[0]}.`}</h2>
          <p>{isAdmin ? "Review incoming journeys, support clients and keep every booking moving." : "Where should business take you next? Your travel team is ready."}</p></div>
          <div className="orbit"><Plane/><span></span></div>
        </section>
        <section className="stats-grid">
          <Stat label="ACTIVE REQUESTS" value={isAdmin ? report.requests ?? 0 : counts.active} detail="Across the travel desk" icon={CalendarDays}/>
          <Stat label="CONFIRMED TRIPS" value={isAdmin ? report.bookings ?? 0 : counts.booked} detail="Ready for departure" icon={Check}/>
          <Stat label={isAdmin ? "ORGANIZATIONS" : "TRAVEL SUPPORT"} value={isAdmin ? report.organizations ?? 0 : "24/7"} detail={isAdmin ? "Active client accounts" : "Agent assistance"} icon={isAdmin ? Building2 : Sparkles}/>
          <Stat label={isAdmin ? "INVOICED" : "SERVICES"} value={isAdmin ? `₹${(report.invoiced_revenue ?? 0).toLocaleString()}` : "5"} detail={isAdmin ? "Platform billing total" : "Flights to events"} icon={CircleDollarSign}/>
        </section>
        <section className="content-grid">
          <div className="panel wide">
            <div className="panel-title"><div><span className="kicker">LIVE WORKFLOW</span><h3>Recent travel requests</h3></div><button onClick={() => setPage("Travel requests")}>View all <ChevronRight/></button></div>
            <RequestTable requests={requests.slice(0, 5)} onEdit={setEditing} client={!isAdmin}/>
          </div>
          <div className="panel quick">
            <span className="kicker">START A JOURNEY</span><h3>What do you need?</h3>
            <div className="service-grid">{SERVICES.map(({id,label,icon:Icon,color}) =>
              <button key={id} onClick={() => setShowRequest(true)} style={{"--accent": color}}><span><Icon/></span>{label}</button>)}</div>
          </div>
        </section>
      </>}

      {page === "Travel requests" && <section className="panel page-panel">
        <div className="panel-title"><div><span className="kicker">ALL JOURNEYS</span><h3>Travel request queue</h3></div><button className="primary compact" onClick={() => setShowRequest(true)}><Plus/> Create</button></div>
        <RequestTable requests={requests} onEdit={setEditing} client={!isAdmin}/>
      </section>}

      {page === "Organizations" && <section className="panel page-panel">
        <div className="panel-title"><div><span className="kicker">B2B ACCOUNTS</span><h3>Client organizations</h3></div><button className="primary compact" onClick={()=>setShowOnboard(true)}><Plus/> Onboard</button></div>
        <div className="org-grid">{organizations.map(org => <article key={org.id}><span><Building2/></span><div><b>{org.name}</b><small>{org.code} · {org.billing_email}</small></div><em>{org.active ? "Active" : "Paused"}</em></article>)}</div>
      </section>}

      {page === "My profile" && <ProfilePanel token={token} initial={user}/>}
      {["Bookings","Travelers","Reports"].includes(page) && <section className="panel empty-state">
        <Sparkles/><span className="kicker">CONNECTED MODULE</span><h2>{page}</h2>
        <p>This workspace is backed by live API endpoints and ready for the next product iteration.</p>
        <button className="primary" onClick={() => setPage("Overview")}>Return to overview</button>
      </section>}
    </main>
    {showRequest && <RequestModal token={token} close={() => setShowRequest(false)} saved={load}/>}
    {editing && <EditRequestModal token={token} request={editing} close={()=>setEditing(null)} saved={load}/>}
    {showOnboard && <OnboardModal token={token} organizations={organizations} close={()=>setShowOnboard(false)} saved={load}/>}
  </div>;
}

function RequestTable({ requests, onEdit, client }) {
  if (!requests.length) return <div className="table-empty"><CalendarDays/><p>No travel requests yet.</p></div>;
  return <div className="table-wrap"><table><thead><tr><th>Reference</th><th>Journey</th><th>Service</th><th>Dates</th><th>Status</th>{client&&<th></th>}</tr></thead>
    <tbody>{requests.map(item => <tr key={item.id}><td><b>{item.reference}</b></td><td>{item.origin || "—"} <ChevronRight/> {item.destination}</td><td className="capitalize">{item.service_type}</td><td>{item.start_date}<small> to {item.end_date}</small></td><td><span className={`status ${item.status}`}>{item.status}</span></td>{client&&<td><button className="edit-link" disabled={!["submitted","reviewing"].includes(item.status)} onClick={()=>onEdit(item)}>Edit</button></td>}</tr>)}</tbody></table></div>;
}

export default function App() {
  const [session, setSession] = useState(() => {
    try { return JSON.parse(localStorage.getItem("voyage-session")) || null; } catch { return null; }
  });
  const login = data => { localStorage.setItem("voyage-session", JSON.stringify(data)); setSession(data); };
  const logout = () => { localStorage.removeItem("voyage-session"); setSession(null); };
  return session ? <Dashboard session={session} logout={logout}/> : <Login onLogin={login}/>;
}
