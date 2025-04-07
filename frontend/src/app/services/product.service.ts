import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { AuthService } from './auth.service';

@Injectable({
  providedIn: 'root'
})
export class ProductService {
  private apiUrl = 'http://localhost:8000';  // 改為正確的API路徑

  constructor(
    private http: HttpClient,
    private authService: AuthService
  ) { }

  // 主要方法，保留原始名稱以保持兼容性
  compareProducts(query: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/api/search`, 
      { content: query },
      { headers: this.authService.getAuthHeaders() }
    ).pipe(
      catchError(this.handleError)
    );
  }
  
  // 作為旅遊查詢的別名方法
  travelQuery(query: string): Observable<any> {
    return this.compareProducts(query); // 實際上調用相同的方法
  }

  private handleError(error: any) {
    let errorMessage = 'An error occurred while processing your request';
    if (error.error instanceof ErrorEvent) {
      // Client-side error
      errorMessage = error.error.message;
    } else {
      // Server-side error
      errorMessage = error.error?.detail || error.error?.error || `Error Code: ${error.status}\nMessage: ${error.message}`;
    }
    console.error(errorMessage);
    return throwError(() => new Error(errorMessage));
  }
}