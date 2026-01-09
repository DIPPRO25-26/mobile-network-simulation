import "./App.css";
import GenerateForm from "./components/GenerateForm.jsx";
import ReplayForm from "./components/ReplayForm.jsx";
import ConnectForm from "./components/ConnectForm.jsx";

export default function App() {
  return (
    <>
      <header className="app-header">
        <h1>Simulator</h1>
        <p>Generate, replay i manual connect </p>
      </header>

      <main>
        <GenerateForm />
        <ReplayForm />
        <ConnectForm />
      </main>
    </>
  );
}
