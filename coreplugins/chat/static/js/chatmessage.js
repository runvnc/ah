import {LitElement, html, css} from './lit-core.min.js';
import {BaseEl} from './base.js'
import { unsafeHTML } from './unsafe-html.js';

export class ChatMessage extends BaseEl {
  static properties = {
    sender: {type: String},
    persona: {type: String},
    spinning : {type: String}
  }

  static styles = [ css`
  ` ]

  constructor() {
    super()
    this.sender = 'user'
    this.persona = 'user'
    this.spinning = 'no'
  }

  _render() {
    return html`
    <div class="outer-msg">
      <img class="avatar hover-zoom" onerror="this.style.display='none'" src="/static/personas/${this.persona}/avatar.png" alt="avatar">
      <div class="message msg-${this.sender}">
        <slot></slot>
      </div>
    </div>
    <div class="spinner ${this.spinning=='yes' ? 'show' : ''}"></div>
    <div class="spacer"></div>
  `
  }
}

customElements.define('chat-message', ChatMessage)

