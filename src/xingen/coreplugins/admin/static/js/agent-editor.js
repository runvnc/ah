import { LitElement, html, css } from './lit-core.min.js';
import { BaseEl } from './base.js';
import './toggle-switch.js';

class AgentEditor extends BaseEl {
  static properties = {
    agent: { type: Object },
    scope: { type: String },
    name: { type: String },
    agents: { type: Array },
    newAgent: { type: Boolean },
    personas: { type: Array },
    commands: { type: Array },
    importStatus: { type: String },
    githubImportStatus: { type: String },
    loading: { type: Boolean },
    errorMessage: { type: String }
  };

  static styles = [
    css`
      :host {
        display: block;
      }
      .loading {
        opacity: 0.7;
        pointer-events: none;
      }
      .error-message {
        color: #e57373;
        margin: 1rem 0;
        padding: 0.75rem;
        border: 1px solid rgba(244, 67, 54, 0.2);
        border-radius: 4px;
        background: rgba(244, 67, 54, 0.1);
      }
      .required::after {
        content: " *";
        color: #e57373;
      }
      .tooltip {
        position: relative;
        display: inline-block;
      }
      .tooltip .tooltip-text {
        visibility: hidden;
        background-color: rgba(0, 0, 0, 0.8);
        color: #fff;
        text-align: center;
        padding: 5px 10px;
        border-radius: 6px;
        position: absolute;
        z-index: 1;
        bottom: 125%;
        left: 50%;
        transform: translateX(-50%);
        white-space: nowrap;
      }
      .tooltip:hover .tooltip-text {
        visibility: visible;
      }
    `
  ];

  constructor() {
    super();
    this.agent = {};
    this.agents = [];
    this.personas = [];
    this.commands = [];
    this.scope = 'local';
    this.newAgent = false;
    this.importStatus = '';
    this.githubImportStatus = '';
    this.loading = false;
    this.errorMessage = '';
    this.fetchPersonas();
    this.fetchCommands();
  }

  connectedCallback() {
    super.connectedCallback();
    this.fetchAgents();
  }

  async fetchPersonas() {
    try {
      this.loading = true;
      const response = await fetch(`/personas/${this.scope}`);
      if (!response.ok) throw new Error('Failed to fetch personas');
      this.personas = await response.json();
    } catch (error) {
      this.errorMessage = `Error loading personas: ${error.message}`;
    } finally {
      this.loading = false;
    }
  }

  async fetchCommands() {
    try {
      this.loading = true;
      const response = await fetch(`/commands`);
      if (!response.ok) throw new Error('Failed to fetch commands');
      const data = await response.json();
      this.commands = this.organizeCommands(data);
    } catch (error) {
      this.errorMessage = `Error loading commands: ${error.message}`;
    } finally {
      this.loading = false;
    }
  }

  organizeCommands(commands) {
    // Group commands by category based on their prefix
    const grouped = commands.reduce((acc, cmd) => {
      const category = cmd.split('_')[0] || 'Other';
      if (!acc[category]) acc[category] = [];
      acc[category].push(cmd);
      return acc;
    }, {});
    return grouped;
  }

  async fetchAgents() {
    try {
      this.loading = true;
      const response = await fetch(`/agents/${this.scope}`);
      if (!response.ok) throw new Error('Failed to fetch agents');
      this.agents = await response.json();
    } catch (error) {
      this.errorMessage = `Error loading agents: ${error.message}`;
    } finally {
      this.loading = false;
    }
  }

  async fetchAgent() {
    if (!this.newAgent && this.name) {
      try {
        this.loading = true;
        const response = await fetch(`/agents/${this.scope}/${this.name}`);
        if (!response.ok) throw new Error('Failed to fetch agent');
        this.agent = await response.json();
        this.agent.uncensored = this.agent.flags.includes('uncensored');
      } catch (error) {
        this.errorMessage = `Error loading agent: ${error.message}`;
      } finally {
        this.loading = false;
      }
    } else {
      this.agent = {};
    }
  }

  validateForm() {
    if (!this.agent.name?.trim()) {
      this.errorMessage = 'Name is required';
      return false;
    }
    if (!this.agent.persona?.trim()) {
      this.errorMessage = 'Persona is required';
      return false;
    }
    if (!this.agent.instructions?.trim()) {
      this.errorMessage = 'Instructions are required';
      return false;
    }
    return true;
  }

  handleScopeChange(event) {
    this.scope = event.target.value;
    this.fetchAgents();
  }

  handleAgentChange(event) {
    if (confirm('Loading a different agent will discard any unsaved changes. Continue?')) {
      this.name = event.target.value;
      this.newAgent = false;
      this.fetchAgent();
    }
  }

  handleNewAgent() {
    if (confirm('Creating a new agent will discard any unsaved changes. Continue?')) {
      this.newAgent = true;
      this.agent = {};
    }
  }

  handleInputChange(event) {
    const { name, value, type, checked } = event.target;
    const inputValue = type === 'checkbox' ? checked : value;
    
    if (name === 'commands') {
      if (!Array.isArray(this.agent.commands)) {
        this.agent.commands = [];
      }
      if (checked) {
        this.agent.commands.push(value);
      } else {
        this.agent.commands = this.agent.commands.filter(command => command !== value);
      }
    } else {
      this.agent = { ...this.agent, [name]: inputValue };
    }
    this.errorMessage = ''; // Clear error when user makes changes
  }

  async handleSubmit(event) {
    event.preventDefault();
    
    if (!this.validateForm()) return;

    try {
      this.loading = true;
      const method = this.newAgent ? 'POST' : 'PUT';
      const url = this.newAgent ? `/agents/${this.scope}` : `/agents/${this.scope}/${this.name}`;
      
      const formData = new FormData();
      this.agent.flags = [];
      if (this.agent.uncensored) {
        this.agent.flags.push('uncensored');
      }
      
      formData.append('agent', JSON.stringify(this.agent));
      
      const response = await fetch(url, {
        method,
        body: formData
      });

      if (!response.ok) throw new Error('Failed to save agent');
      
      this.importStatus = 'Agent saved successfully';
      this.newAgent = false;
      await this.fetchAgents();
      
      setTimeout(() => {
        this.importStatus = '';
      }, 3000);
    } catch (error) {
      this.errorMessage = `Error saving agent: ${error.message}`;
    } finally {
      this.loading = false;
    }
  }

  async handleScanAndImport() {
    const directory = prompt("Enter the directory path to scan for agents:");
    if (!directory) return;

    try {
      this.loading = true;
      const response = await fetch('/scan-and-import-agents', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ directory, scope: this.scope })
      });

      const result = await response.json();
      if (result.success) {
        this.importStatus = `Success: Imported ${result.imported_agents.length} agents`;
        await this.fetchAgents();
      } else {
        this.importStatus = `Error: ${result.message}`;
      }
    } catch (error) {
      this.importStatus = `Error: ${error.message}`;
    } finally {
      this.loading = false;
      setTimeout(() => {
        this.importStatus = '';
      }, 5000);
    }
  }

  async handleGitHubImport() {
    const repoPath = this.shadowRoot.querySelector('#githubRepo').value;
    const tag = this.shadowRoot.querySelector('#githubTag').value;

    if (!repoPath) {
      this.githubImportStatus = 'Error: Repository path is required';
      return;
    }

    try {
      this.loading = true;
      const response = await fetch('/import-github-agent', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          repo_path: repoPath,
          scope: this.scope,
          tag: tag || null
        })
      });

      const result = await response.json();
      if (response.ok) {
        this.githubImportStatus = `Success: ${result.message}`;
        await this.fetchAgents();
      } else {
        this.githubImportStatus = `Error: ${result.detail || result.message}`;
      }
    } catch (error) {
      this.githubImportStatus = `Error: ${error.message}`;
    } finally {
      this.loading = false;
      setTimeout(() => {
        this.githubImportStatus = '';
      }, 5000);
    }
  }

  renderCommands() {
    return Object.entries(this.commands).map(([category, cmds]) => html`
      <div class="commands-category">
        <h4>${category}</h4>
        <div class="commands-grid">
          ${cmds.map(command => html`
            <div class="command-item">
              <input type="checkbox" 
                     name="commands" 
                     value="${command}" 
                     .checked=${this.agent.commands?.includes(command)}
                     @change=${this.handleInputChange} />
              <span class="tooltip">
                ${command}
                <span class="tooltip-text">Click to toggle this command</span>
              </span>
            </div>
          `)}
        </div>
      </div>
    `);
  }

  _render() {
    return html`
      <div class="agent-editor ${this.loading ? 'loading' : ''}">
        ${this.errorMessage ? html`
          <div class="error-message">${this.errorMessage}</div>
        ` : ''}
        
        <div class="scope-selector">
          <label>
            <input type="radio" name="scope" value="local" 
                   .checked=${this.scope === 'local'} 
                   @change=${this.handleScopeChange} /> Local
          </label>
          <label>
            <input type="radio" name="scope" value="shared" 
                   .checked=${this.scope === 'shared'} 
                   @change=${this.handleScopeChange} /> Shared
          </label>
        </div>

        <div class="agent-selector">
          <select @change=${this.handleAgentChange} 
                  .value=${this.name || ''} 
                  ?disabled=${this.newAgent}>
            <option value="">Select an agent</option>
            ${this.agents.map(agent => html`
              <option value="${agent.name}">${agent.name}</option>
            `)}
          </select>
          <button class="btn btn-secondary" @click=${this.handleNewAgent}>New Agent</button>
          <button class="btn btn-secondary" @click=${this.handleScanAndImport}>
            Scan and Import Agents
          </button>
        </div>

        ${this.importStatus ? html`
          <div class="status-message ${this.importStatus.startsWith('Success') ? 'success' : 'error'}">
            ${this.importStatus}
          </div>
        ` : ''}

        <div class="github-import">
          <h3>Import from GitHub</h3>
          <div class="github-import-form">
            <input type="text" id="githubRepo" 
                   placeholder="owner/repository" 
                   class="tooltip">
            <input type="text" id="githubTag" 
                   placeholder="tag (optional)" 
                   class="tooltip">
            <button class="btn btn-secondary" 
                    @click=${this.handleGitHubImport}>Import from GitHub</button>
          </div>
          ${this.githubImportStatus ? html`
            <div class="status-message ${this.githubImportStatus.startsWith('Success') ? 'success' : 'error'}">
              ${this.githubImportStatus}
            </div>
          ` : ''}
        </div>

        <form @submit=${this.handleSubmit} class="agent-form">
          <div class="form-group">
            <label class="required">Name:</label>
            <input type="text" name="name" 
                   .value=${this.agent.name || ''} 
                   @input=${this.handleInputChange} 
                   class="tooltip">
          </div>

          <div class="form-group">
            <label class="required">Persona:</label>
            <select name="persona" 
                    .value=${this.agent.persona || ''} 
                    @input=${this.handleInputChange}>
              <option value="">Select a persona</option>
              ${this.personas.map(persona => html`
                <option value="${persona.name}">${persona.name}</option>
              `)}
            </select>
          </div>

          <div class="form-group">
            <label class="required">Instructions:</label>
            <textarea name="instructions" 
                      rows="20" 
                      .value=${this.agent.instructions || ''} 
                      @input=${this.handleInputChange}></textarea>
          </div>

          <div class="form-group">
            <label>
              Uncensored:
              <toggle-switch 
                .checked=${this.agent.uncensored || false}
                @toggle-change=${(e) => {
                  this.handleInputChange({
                    target: {
                      name: 'uncensored',
                      checked: e.detail.checked,
                      type: 'checkbox'
                    }
                  });
                }}></toggle-switch>
            </label>
          </div>

          <div class="form-group commands-section">
            <label>Commands:</label>
            ${this.renderCommands()}
          </div>

          <button class="btn" type="submit" ?disabled=${this.loading}>
            ${this.loading ? 'Saving...' : 'Save'}
          </button>
        </form>
      </div>
    `;
  }
}

customElements.define('agent-editor', AgentEditor);
