import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ProductService } from '../../services/product.service';
import { MessageService } from '../../services/message/message.service';
import { LoadingSpinnerComponent } from '../shared/loading-spinner/loading-spinner.component';

@Component({
  selector: 'app-product-comparison',
  standalone: true,
  imports: [CommonModule, FormsModule, LoadingSpinnerComponent],
  templateUrl: './product-comparison.component.html',
  styleUrls: ['./product-comparison.component.css']
})
export class ProductComparisonComponent {
  query: string = '';
  chatMessages: any[] = [];
  errorMessage: string = '';
  isLoading: boolean = false;
  showExamples: boolean = true;
  queryExamples: string[] = [
    '我想去陽明山一日遊，請問有哪些推薦的景點?',
    '有哪些適合帶家人遊玩的花蓮景點',
    '晚上想去逛夜市，請推薦我桃園的夜市'
  ];

  constructor(
    private productService: ProductService,
    private messageService: MessageService
  ) {}

  submitQuery() {
    if (!this.query.trim()) {
      this.messageService.warning('請輸入查詢內容');
      return;
    }

    this.isLoading = true;
    this.errorMessage = '';
    this.showExamples = false;
    
    // 添加用戶消息到聊天記錄
    this.chatMessages.push({
      type: 'user',
      content: this.query
    });
    
    const currentQuery = this.query;
    this.query = ''; // 清空輸入框

    this.productService.compareProducts(currentQuery).subscribe({
      next: (response) => {
        this.isLoading = false;
        
        // 添加系統回覆到聊天記錄
        if (response.response) {
          this.chatMessages.push({
            type: 'system',
            content: response.response
          });
        } else if (response.error) {
          this.chatMessages.push({
            type: 'error',
            content: response.error
          });
        }
        
        this.messageService.success('查詢成功');
      },
      error: (error) => {
        this.errorMessage = error.message || '查詢處理時發生錯誤';
        
        // 添加錯誤消息到聊天記錄
        this.chatMessages.push({
          type: 'error',
          content: this.errorMessage
        });
        
        this.messageService.error(this.errorMessage);
        this.isLoading = false;
      }
    });
  }

  useExample(example: string) {
    this.query = example;
    this.submitQuery();
  }

  resetChat() {
    this.query = '';
    this.chatMessages = [];
    this.errorMessage = '';
    this.showExamples = true;
  }
}
