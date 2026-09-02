import { ComponentFixture, TestBed } from '@angular/core/testing';
import { PortfolioListPage } from './portfolio-list-page';

describe('PortfolioListPage', () => {
  let component: PortfolioListPage;
  let fixture: ComponentFixture<PortfolioListPage>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [PortfolioListPage],
    }).compileComponents();

    fixture = TestBed.createComponent(PortfolioListPage);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
