import { Component } from '@angular/core';
import { PortfolioRead } from '../../../../core/api/models/portfolio-model';

@Component({
  imports: [],
  selector: 'app-portfolio-form-dialog',
  styleUrls: ['./portfolio-form-dialog.scss'],
  templateUrl: './portfolio-form-dialog.html',
})
export class PortfolioFormDialog {
  mode: 'create' | 'edit' = 'create';
  portfolio?: PortfolioRead;
}
