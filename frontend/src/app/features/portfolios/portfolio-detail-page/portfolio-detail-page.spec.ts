import { ComponentFixture, TestBed } from '@angular/core/testing';
import { PortfolioDetailPage } from './portfolio-detail-page';

describe('PortfolioDetailPage', () => {
  let component: PortfolioDetailPage;
  let fixture: ComponentFixture<PortfolioDetailPage>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [PortfolioDetailPage],
    }).compileComponents();

    fixture = TestBed.createComponent(PortfolioDetailPage);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
