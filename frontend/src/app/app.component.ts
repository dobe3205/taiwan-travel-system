import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { HeaderComponent } from './components/header/header.component';
import { MessageComponent } from './components/shared/message/message.component';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, HeaderComponent, MessageComponent],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css',
  standalone: true
})
export class AppComponent {
  title = '台灣旅遊助手';
}
